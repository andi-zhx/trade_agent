"""The default workflow: one shared enterprise library and its products."""
from datetime import datetime
from pathlib import Path
import re
import uuid

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError

from models import AuditLog, Document, Enterprise, Product, db
from web_security import require_admin

entry = Blueprint("entry", __name__, url_prefix="/library")
ENTERPRISE_FIELDS = [("company_name", "企业名称", 255), ("province", "省份", 50), ("city", "城市", 50), ("industry_category", "所属行业", 100), ("business_address", "地址", 255), ("main_products", "主营产品", 4000)]
CONTACT_FIELDS = [("primary_contact_name", "联系人", 100), ("primary_contact_mobile", "联系电话", 50), ("contact_email", "联系邮箱", 120)]
PRODUCT_FIELDS = [("product_name_cn", "产品名称", 255), ("model", "型号 / 规格", 100), ("product_category", "产品分类", 100), ("moq", "起订量", 50), ("average_price", "参考价格", 255), ("function_description", "产品介绍", 6000), ("notes", "备注", 6000)]


def record(action, item):
    db.session.add(AuditLog(action=action, target_type="enterprise" if isinstance(item, Enterprise) else "product", target_id=item.id, user_name=g.user.username))


def read_fields(fields):
    values = {}
    for key, label, limit in fields:
        value = request.form.get(key, "").strip()
        if len(value) > limit:
            raise ValueError(f"{label}最多填写 {limit} 个字符。")
        values[key] = value
    return values


def check_version(item):
    if request.form.get("version_id", type=int) != item.version_id:
        raise StaleDataError("此资料已由其他人修改；本次填写内容保留在页面中，请先另开页面核对最新资料，避免覆盖。")


def saved_location(item):
    if isinstance(item, Enterprise):
        return url_for("entry.enterprise", id=item.id)
    return url_for("entry.enterprise", id=item.enterprise_id) + f"#product-{item.id}"


@entry.get("")
@entry.get("/")
def home():
    keyword = request.args.get("q", "").strip()
    query = Enterprise.query
    if keyword:
        query = query.filter(or_(Enterprise.company_name.contains(keyword, autoescape=True), Enterprise.enterprise_code.contains(keyword, autoescape=True), Enterprise.main_products.contains(keyword, autoescape=True)))
    page = query.order_by(Enterprise.updated_at.desc(), Enterprise.id.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    return render_template("library/home.html", page=page, keyword=keyword)


@entry.get("/products")
def products():
    keyword = request.args.get("q", "").strip()
    query = Product.query.join(Enterprise)
    if keyword:
        query = query.filter(or_(Product.product_name_cn.contains(keyword, autoescape=True), Product.model.contains(keyword, autoescape=True), Enterprise.company_name.contains(keyword, autoescape=True)))
    page = query.order_by(Product.updated_at.desc(), Product.id.desc()).paginate(page=request.args.get("page", 1, type=int), per_page=20, error_out=False)
    return render_template("library/products.html", page=page, keyword=keyword)


@entry.get("/enterprises/<int:id>")
def enterprise(id):
    item = Enterprise.query.filter_by(id=id).first_or_404()
    return render_template("library/enterprise.html", item=item, products=Product.query.filter_by(enterprise_id=id).order_by(Product.updated_at.desc()).all(), documents=Document.query.filter_by(enterprise_id=id, product_id=None).all())


def edit_form(model, id=None):
    is_enterprise = model is Enterprise
    item = model.query.filter_by(id=id).first_or_404() if id else None
    status = 200
    error = None
    created_files = []
    submission_key = request.form.get("submission_key", "") if request.method == "POST" else uuid.uuid4().hex
    if request.method == "POST":
        try:
            if item:
                check_version(item)
            else:
                if not re.fullmatch(r"[a-f0-9]{32}", submission_key):
                    raise ValueError("页面已失效，请重新打开新增页面。")
                previous = model.query.execution_options(include_deleted=True).filter_by(submission_key=submission_key).first()
                if previous:
                    if previous.is_deleted:
                        raise ValueError("此条资料已保存后移至回收站，请联系管理员恢复。")
                    flash("这次提交已经保存，无需重复提交。", "info")
                    return redirect(saved_location(previous))
            fields = read_fields(ENTERPRISE_FIELDS if is_enterprise else PRODUCT_FIELDS)
            if not fields["company_name" if is_enterprise else "product_name_cn"]:
                raise ValueError("请填写企业名称。" if is_enterprise else "请填写产品名称。")
            if not is_enterprise:
                parent = Enterprise.query.filter_by(id=request.form.get("enterprise_id", type=int)).first()
                if not parent:
                    raise ValueError("请先选择一个已保存的企业。")
                # An existing product stays with its enterprise, including all its attachments.
                if item and parent.id != item.enterprise_id:
                    raise ValueError("已有产品的所属企业不能在简洁表单中变更。")
            if item is None:
                item = model(submission_key=submission_key)
                setattr(item, "enterprise_code" if is_enterprise else "product_code", ("E" if is_enterprise else "P") + submission_key[:24].upper())
                db.session.add(item)
            for key, value in fields.items():
                setattr(item, key, value)
            if is_enterprise:
                extra = dict(item.enterprise_extra_fields or {})
                extra.update(read_fields(CONTACT_FIELDS))
                extra.update(company_full_name=item.company_name, core_products=item.main_products, business_address=item.business_address)
                item.enterprise_extra_fields = extra
            else:
                item.enterprise_id = parent.id
                if not id:
                    item.industry_code, item.industry_name = parent.industry_code, parent.industry_category
            item.updated_at = datetime.utcnow()
            db.session.flush()
            from app import 保存文件并登记记录
            for upload in request.files.getlist("attachments"):
                if upload.filename:
                    document = 保存文件并登记记录(current_app, item if is_enterprise else parent, None if is_enterprise else item, upload, "其他", Path(upload.filename).name, g.user.username)
                    created_files.append(current_app.config["DATA_ROOT"] / document.file_path)
            record("保存企业" if is_enterprise else "保存产品", item)
            db.session.commit()
            flash("保存成功，资料已存入资料库。", "success")
            if is_enterprise and request.form.get("next_step") == "product":
                return redirect(url_for("entry.product_new", enterprise_id=item.id))
            return redirect(saved_location(item))
        except (ValueError, IntegrityError, StaleDataError, OperationalError, OSError) as exc:
            db.session.rollback()
            for path in created_files:
                path.unlink(missing_ok=True)
            if isinstance(exc, IntegrityError) and not id:
                previous = model.query.execution_options(include_deleted=True).filter_by(submission_key=submission_key, is_deleted=False).first()
                if previous:
                    return redirect(saved_location(previous))
            status = 409 if isinstance(exc, (IntegrityError, StaleDataError)) else 400
            error = str(exc) if isinstance(exc, ValueError) else ("资料已被其他成员修改或保存。你的输入仍保留在此页面，请另开页面核对最新资料后再编辑。" if status == 409 else "保存未完成，可能是服务繁忙或存储异常。你的输入仍保留在此页面，请稍后重试。")
            if not isinstance(exc, (ValueError, StaleDataError)):
                current_app.logger.exception("资料保存失败")
            item = model.query.filter_by(id=id).first() if id else None
    values = dict(request.form) if request.method == "POST" else {key: (getattr(item, key, None) or "") for key, _, _ in (ENTERPRISE_FIELDS if is_enterprise else PRODUCT_FIELDS)}
    if request.method != "POST" and is_enterprise:
        values.update({key: (item.enterprise_extra_fields or {}).get(key, "") if item else "" for key, _, _ in CONTACT_FIELDS})
    parent_id = request.form.get("enterprise_id", type=int) or (item.enterprise_id if item and not is_enterprise else request.args.get("enterprise_id", type=int))
    documents = Document.query.filter_by(**({"enterprise_id": id, "product_id": None} if is_enterprise else {"product_id": id})).all() if id else []
    return render_template("library/form.html", item=item, is_enterprise=is_enterprise, values=values, error=error, submission_key=submission_key, conflict=status == 409,
                           fields=ENTERPRISE_FIELDS if is_enterprise else PRODUCT_FIELDS, contact_fields=CONTACT_FIELDS, enterprises=Enterprise.query.order_by(Enterprise.company_name).all() if not is_enterprise else [], parent_id=parent_id, documents=documents), status


@entry.route("/enterprises/new", methods=["GET", "POST"])
def enterprise_new():
    return edit_form(Enterprise)


@entry.route("/enterprises/<int:id>/edit", methods=["GET", "POST"])
def enterprise_edit(id):
    return edit_form(Enterprise, id)


@entry.route("/products/new", methods=["GET", "POST"])
def product_new():
    return edit_form(Product)


@entry.route("/products/<int:id>/edit", methods=["GET", "POST"])
def product_edit(id):
    product = Product.query.filter_by(id=id).first_or_404()
    Enterprise.query.filter_by(id=product.enterprise_id).first_or_404()
    return edit_form(Product, id)


@entry.post("/<kind>/<int:id>/archive")
def archive(kind, id):
    require_admin()
    model = {"enterprises": Enterprise, "products": Product}.get(kind)
    if not model:
        abort(404)
    item = model.query.filter_by(id=id).first_or_404()
    try:
        check_version(item)
        item.soft_delete(g.user.username)
        record("移入回收站", item)
        db.session.commit()
    except StaleDataError:
        db.session.rollback()
        return render_template("request_error.html", message="资料已被修改，请刷新后确认要移入回收站的资料。"), 409
    flash("已移入回收站；管理员可恢复，附件仍然保留。", "success")
    return redirect(url_for("entry.home"))


@entry.route("/trash", methods=["GET", "POST"])
def trash():
    require_admin()
    if request.method == "POST":
        model = {"enterprise": Enterprise, "product": Product}.get(request.form.get("kind"))
        if not model:
            abort(400)
        item = model.query.execution_options(include_deleted=True).filter_by(id=request.form.get("id", type=int), is_deleted=True).first_or_404()
        if model is Product and not Enterprise.query.filter_by(id=item.enterprise_id).first():
            flash("请先恢复此产品所属的企业。", "warning")
        else:
            item.is_deleted, item.deleted_at = False, None
            record("恢复资料", item)
            db.session.commit()
            flash("资料已恢复。", "success")
        return redirect(url_for("entry.trash"))
    return render_template("library/trash.html", enterprises=Enterprise.query.execution_options(include_deleted=True).filter_by(is_deleted=True).all(), products=Product.query.execution_options(include_deleted=True).filter_by(is_deleted=True).all())
