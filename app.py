from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO
import csv
import shutil
from pathlib import Path
import re
from functools import wraps
from zipfile import ZIP_DEFLATED, ZipFile

from flask import Flask, flash, redirect, render_template, request, send_file, send_from_directory, session, url_for
from sqlalchemy import func, or_
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from models import (
    Contact,
    Demand,
    Document,
    Enterprise,
    EnterpriseAnalysisNote,
    ForeignClient,
    MatchRecord,
    Product,
    ProjectProgress,
    Qualification,
    AuditLog,
    User,
    db,
)

BASE_DIR = Path(__file__).resolve().parent
PER_PAGE = 10
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".jpg", ".png", ".mp4"}
BLOCKED_EXTENSIONS = {".exe", ".bat", ".js", ".sh", ".cmd", ".com", ".msi", ".ps1"}
MAX_UPLOAD_SIZE = 100 * 1024 * 1024


PRODUCT_FORM_SECTIONS = [
    ("A", "所属企业"),
    ("B", "产品基础信息"),
    ("C", "规格参数"),
    ("D", "生产与供货能力"),
    ("E", "价格与贸易条款"),
    ("F", "认证与合规"),
    ("G", "包装与物流"),
    ("H", "市场与卖点"),
    ("I", "售后与备注"),
]

DOCUMENT_TYPE_OPTIONS = [
    ("BASE", "BASE 企业基础信息"),
    ("CERT", "CERT 资质证照"),
    ("FIN", "FIN 经营财务"),
    ("TRADE", "TRADE 外贸能力"),
    ("PROD", "PROD 产品信息"),
    ("SPEC", "SPEC 产品规格书"),
    ("IMG", "IMG 图片"),
    ("VIDEO", "VIDEO 视频"),
    ("PPT", "PPT 宣传PPT"),
    ("MIN", "MIN 会议纪要"),
    ("CONTRACT", "CONTRACT 合同协议"),
    ("AUTH", "AUTH 授权文件"),
    ("REVIEW", "REVIEW 审核归档"),
    ("QUOTE", "QUOTE 报价单"),
    ("SAMPLE", "SAMPLE 样品资料"),
    ("OTHER", "OTHER 其他"),
]

DOCUMENT_FOLDER_MAPPING = {
    "BASE": "01_企业基础信息",
    "CERT": "02_企业资质证照",
    "FIN": "03_经营财务资料",
    "TRADE": "04_外贸能力与交易记录",
    "PROD": "05_产品资料",
    "SPEC": "05_产品资料",
    "PPT": "06_宣传展示材料",
    "MIN": "07_项目沟通与会议记录",
    "IMG": "08_影像资料",
    "VIDEO": "08_影像资料",
    "CONTRACT": "09_合同协议与授权文件",
    "AUTH": "09_合同协议与授权文件",
    "REVIEW": "10_审核归档文件",
    "QUOTE": "10_审核归档文件",
    "SAMPLE": "10_审核归档文件",
    "OTHER": "11_其他资料",
}

PROJECT_STAGE_OPTIONS = [
    "待补充资料",
    "已完成入库",
    "已推荐给外资",
    "外资初步感兴趣",
    "已发送资料",
    "已寄送样品",
    "已报价",
    "商务谈判中",
    "合同签署中",
    "已成交",
    "暂停/终止",
]

SAMPLE_STATUS_OPTIONS = [
    "未涉及",
    "待寄样",
    "已寄样",
    "样品反馈中",
    "样品通过",
    "样品未通过",
]

QUOTATION_STATUS_OPTIONS = [
    "未报价",
    "已初步报价",
    "已更新报价",
    "报价接受",
    "报价未接受",
]

CONTRACT_STATUS_OPTIONS = [
    "未开始",
    "起草中",
    "审核中",
    "已签署",
    "未成交",
]


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "replace-with-a-secure-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'trade_agent.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_ROOT"] = BASE_DIR / "uploads" / "企业库"
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
    app.config["BACKUP_ROOT"] = BASE_DIR / "backups"

    db.init_app(app)

    def 当前用户():
        用户名 = session.get("用户")
        if not 用户名:
            return None
        return User.query.filter_by(username=用户名).first()

    def 记录审计日志(action, target_type, target_id=None, detail=None):
        用户 = 当前用户()
        db.session.add(
            AuditLog(
                action=action,
                target_type=target_type,
                target_id=target_id,
                user_name=用户.username if 用户 else "system",
                detail=detail,
            )
        )

    def login_required(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not session.get("用户"):
                flash("请先登录后再访问。", "warning")
                return redirect(url_for("登录"))
            return view_func(*args, **kwargs)

        return wrapped

    def admin_required(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            用户 = 当前用户()
            if not 用户:
                flash("请先登录后再访问。", "warning")
                return redirect(url_for("登录"))
            if 用户.role != "管理员":
                flash("仅管理员可执行此操作。", "danger")
                return redirect(url_for("dashboard"))
            return view_func(*args, **kwargs)

        return wrapped

    def 构建数据库备份():
        备份目录 = app.config["BACKUP_ROOT"]
        备份目录.mkdir(parents=True, exist_ok=True)
        时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
        源数据库 = BASE_DIR / "trade_agent.db"
        备份路径 = 备份目录 / f"backup_db_{时间戳}.sqlite"
        shutil.copy2(源数据库, 备份路径)
        return 备份路径

    def 构建上传目录备份():
        备份目录 = app.config["BACKUP_ROOT"]
        备份目录.mkdir(parents=True, exist_ok=True)
        时间戳 = datetime.now().strftime("%Y%m%d_%H%M%S")
        备份路径 = 备份目录 / f"backup_uploads_{时间戳}.zip"
        上传根目录 = BASE_DIR / "uploads"
        with ZipFile(备份路径, "w", compression=ZIP_DEFLATED) as zipf:
            if 上传根目录.exists():
                for 文件路径 in 上传根目录.rglob("*"):
                    if 文件路径.is_file():
                        zipf.write(文件路径, arcname=文件路径.relative_to(BASE_DIR))
        return 备份路径

    def 今日是否已有数据库备份():
        today_prefix = f"backup_db_{datetime.now().strftime('%Y%m%d')}"
        return any(path.name.startswith(today_prefix) for path in app.config["BACKUP_ROOT"].glob("backup_db_*.sqlite"))

    @app.template_filter("currency")
    def currency_filter(value, currency="USD"):
        if value is None:
            return "-"
        return f"{currency} {value:,.2f}"

    @app.context_processor
    def inject_user_context():
        return {
            "当前用户名": session.get("用户"),
            "当前角色": session.get("角色"),
            "是管理员": session.get("角色") == "管理员",
        }

    @app.before_request
    def enforce_login():
        if request.endpoint in {"登录", "static"}:
            return None
        if request.endpoint and request.endpoint.startswith("static"):
            return None
        if not session.get("用户"):
            return redirect(url_for("登录"))
        return None

    @app.errorhandler(413)
    def request_entity_too_large(_error):
        flash("上传文件过大，单文件限制为 100MB。", "danger")
        return redirect(url_for("document_upload"))

    @app.route("/")
    def dashboard():
        企业数量 = Enterprise.query.count()
        产品数量 = Product.query.count()
        已上传文件数量 = Document.query.count()
        最近新增企业 = Enterprise.query.order_by(Enterprise.created_at.desc()).limit(5).all()
        最近新增产品 = Product.query.order_by(Product.created_at.desc()).limit(5).all()

        return render_template(
            "dashboard.html",
            企业数量=企业数量,
            产品数量=产品数量,
            已上传文件数量=已上传文件数量,
            最近新增企业=最近新增企业,
            最近新增产品=最近新增产品,
        )

    @app.route("/companies")
    def enterprise_library():
        return redirect(url_for("enterprise_list"))

    @app.route("/products")
    def product_library():
        return redirect(url_for("product_list"))

    @app.route("/backups")
    def backup_management():
        return redirect(url_for("backup_tools"))

    @app.route("/search")
    def global_search():
        q = request.args.get("q", "", type=str).strip()
        results = {"企业": [], "产品": [], "外资需求": [], "文件": []}
        if q:
            like_q = f"%{q}%"
            results["企业"] = Enterprise.query.filter(
                or_(
                    Enterprise.company_name.ilike(like_q),
                    Enterprise.english_name.ilike(like_q),
                    Enterprise.main_products.ilike(like_q),
                )
            ).order_by(Enterprise.updated_at.desc()).limit(50).all()
            results["产品"] = Product.query.filter(
                or_(
                    Product.product_name_cn.ilike(like_q),
                    Product.product_name_en.ilike(like_q),
                    Product.hs_code.ilike(like_q),
                )
            ).order_by(Product.updated_at.desc()).limit(50).all()
            results["外资需求"] = Demand.query.join(ForeignClient, Demand.foreign_client_id == ForeignClient.id).filter(
                or_(
                    ForeignClient.client_name.ilike(like_q),
                    Demand.product_keywords.ilike(like_q),
                    Demand.purchase_category.ilike(like_q),
                )
            ).order_by(Demand.updated_at.desc()).limit(50).all()
            results["文件"] = Document.query.filter(Document.document_name.ilike(like_q)).order_by(Document.uploaded_at.desc()).limit(50).all()

        return render_template("search.html", q=q, results=results)

    @app.get("/excel")
    def excel_tools():
        return render_template("excel_tools.html")

    @app.route("/backup", methods=["GET", "POST"])
    @admin_required
    def backup_tools():
        备份目录 = app.config["BACKUP_ROOT"]
        备份目录.mkdir(parents=True, exist_ok=True)
        if request.method == "POST":
            action = request.form.get("action", "")
            if action == "backup_db":
                文件路径 = 构建数据库备份()
                flash(f"数据库备份成功：{文件路径.name}", "success")
            elif action == "backup_uploads":
                文件路径 = 构建上传目录备份()
                flash(f"上传目录备份成功：{文件路径.name}", "success")
            else:
                flash("未知备份动作。", "danger")
            return redirect(url_for("backup_tools"))
        文件列表 = sorted(备份目录.glob("backup_*"), key=lambda x: x.stat().st_mtime, reverse=True)[:30]
        return render_template("backup.html", files=文件列表)

    @app.get("/excel/export/<string:export_key>")
    def excel_export(export_key):
        try:
            文件名, 表头, 行数据 = 构建导出数据(export_key)
        except ValueError:
            flash("不支持的导出类型。", "danger")
            return redirect(url_for("excel_tools"))
        缓冲区 = BytesIO()
        text_buffer = []
        text_buffer.append(",".join([csv_safe(v) for v in 表头]))
        for row in 行数据:
            text_buffer.append(",".join([csv_safe(v) for v in row]))
        缓冲区.write(("\n".join(text_buffer)).encode("utf-8-sig"))
        缓冲区.seek(0)
        记录审计日志("导出 Excel", "excel", detail=f"export_key={export_key}")
        db.session.commit()
        return send_file(
            缓冲区,
            as_attachment=True,
            download_name=f"{文件名}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mimetype="text/csv",
        )

    @app.route("/excel/import/enterprises", methods=["GET", "POST"])
    def import_enterprises():
        if request.method == "POST":
            上传文件 = request.files.get("file")
            if not 上传文件 or not 上传文件.filename:
                flash("请先选择企业 Excel 文件。", "danger")
                return redirect(url_for("import_enterprises"))
            成功条数, 失败列表 = 导入企业Excel(上传文件)
            记录审计日志("导入 Excel", "enterprise", detail=f"success={成功条数}, failed={len(失败列表)}")
            db.session.commit()
            return render_template("import_result.html", 标题="企业导入结果", 成功条数=成功条数, 失败列表=失败列表)
        return render_template("import_form.html", 标题="企业 Excel 导入", 提示="支持按企业编号更新或新增企业。")

    @app.route("/excel/import/products", methods=["GET", "POST"])
    def import_products():
        if request.method == "POST":
            上传文件 = request.files.get("file")
            if not 上传文件 or not 上传文件.filename:
                flash("请先选择产品 Excel 文件。", "danger")
                return redirect(url_for("import_products"))
            成功条数, 失败列表 = 导入产品Excel(上传文件)
            记录审计日志("导入 Excel", "product", detail=f"success={成功条数}, failed={len(失败列表)}")
            db.session.commit()
            return render_template("import_result.html", 标题="产品导入结果", 成功条数=成功条数, 失败列表=失败列表)
        return render_template("import_form.html", 标题="产品 Excel 导入", 提示="支持按产品编号更新或新增产品。")

    @app.route("/enterprises")
    def enterprise_list():
        page = request.args.get("page", 1, type=int)
        q = request.args.get("q", "", type=str).strip()
        city = request.args.get("city", "", type=str).strip()
        industry = request.args.get("industry", "", type=str).strip()
        manufacturer = request.args.get("manufacturer", "", type=str).strip()
        status = request.args.get("status", "", type=str).strip()

        查询 = Enterprise.query
        if q:
            查询 = 查询.filter(Enterprise.company_name.ilike(f"%{q}%"))
        if city:
            查询 = 查询.filter(Enterprise.city == city)
        if industry:
            查询 = 查询.filter(Enterprise.industry_category == industry)
        if manufacturer in {"yes", "no"}:
            查询 = 查询.filter(Enterprise.is_manufacturer.is_(manufacturer == "yes"))
        if status:
            查询 = 查询.filter(Enterprise.status == status)

        分页 = 查询.order_by(Enterprise.updated_at.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)

        城市列表 = [项[0] for 项 in db.session.query(Enterprise.city).filter(Enterprise.city.isnot(None), Enterprise.city != "").distinct().order_by(Enterprise.city).all()]
        行业列表 = [项[0] for 项 in db.session.query(Enterprise.industry_category).filter(Enterprise.industry_category.isnot(None), Enterprise.industry_category != "").distinct().order_by(Enterprise.industry_category).all()]
        状态列表 = [项[0] for 项 in db.session.query(Enterprise.status).filter(Enterprise.status.isnot(None), Enterprise.status != "").distinct().order_by(Enterprise.status).all()]

        企业ID列表 = [企业.id for 企业 in 分页.items]
        外贸负责人映射 = {}
        if 企业ID列表:
            联系人列表 = Contact.query.filter(Contact.enterprise_id.in_(企业ID列表), Contact.contact_type == "外贸负责人").all()
            for 联系人 in 联系人列表:
                if 联系人.enterprise_id not in 外贸负责人映射:
                    外贸负责人映射[联系人.enterprise_id] = 联系人.name

        return render_template(
            "enterprise_list.html",
            分页=分页,
            筛选={"q": q, "city": city, "industry": industry, "manufacturer": manufacturer, "status": status},
            城市列表=城市列表,
            行业列表=行业列表,
            状态列表=状态列表,
            外贸负责人映射=外贸负责人映射,
        )

    @app.route("/enterprises/new", methods=["GET", "POST"])
    def enterprise_new():
        if request.method == "POST":
            企业 = Enterprise(
                enterprise_code=生成企业编号(),
                company_name=request.form.get("company_name", "").strip(),
                english_name=request.form.get("english_name", "").strip() or None,
                unified_social_credit_code=request.form.get("unified_social_credit_code", "").strip() or None,
                founded_date=读取日期(request.form.get("founded_date")),
                registered_capital=request.form.get("registered_capital", "").strip() or None,
                registered_address=request.form.get("registered_address", "").strip() or None,
                business_address=request.form.get("business_address", "").strip() or None,
                province=request.form.get("province", "").strip() or None,
                city=request.form.get("city", "").strip() or None,
                district=request.form.get("district", "").strip() or None,
                company_type=request.form.get("company_type", "").strip() or None,
                industry_code=request.form.get("industry_code", "").strip() or None,
                industry_category=request.form.get("industry_category", "").strip() or None,
                sub_industry=request.form.get("sub_industry", "").strip() or None,
                main_products=request.form.get("main_products", "").strip() or None,
                main_business=request.form.get("main_business", "").strip() or None,
                is_manufacturer=读取布尔(request.form, "is_manufacturer"),
                is_trader=读取布尔(request.form, "is_trader"),
                is_brand_owner=读取布尔(request.form, "is_brand_owner"),
                is_oem_odm=读取布尔(request.form, "is_oem_odm"),
                is_service_provider=读取布尔(request.form, "is_service_provider"),
                is_high_tech=读取布尔(request.form, "is_high_tech"),
                is_specialized_new=读取布尔(request.form, "is_specialized_new"),
                is_listed_or_pre_ipo=读取布尔(request.form, "is_listed_or_pre_ipo"),
                has_foreign_trade_experience=读取布尔(request.form, "has_foreign_trade_experience"),
                export_countries=request.form.get("export_countries", "").strip() or None,
                target_markets=request.form.get("target_markets", "").strip() or None,
                annual_capacity=request.form.get("annual_capacity", "").strip() or None,
                employee_count=读取整数(request.form.get("employee_count")),
                factory_area=request.form.get("factory_area", "").strip() or None,
                main_equipment=request.form.get("main_equipment", "").strip() or None,
                annual_revenue=读取金额(request.form.get("annual_revenue")),
                export_revenue=读取金额(request.form.get("export_revenue")),
                service_needs=request.form.get("service_needs", "").strip() or None,
                risk_notes=request.form.get("risk_notes", "").strip() or None,
                status=request.form.get("status", "草稿").strip() or "草稿",
                project_owner=request.form.get("project_owner", "").strip() or None,
            )

            外贸负责人 = request.form.get("trade_owner", "").strip()

            if not 企业.company_name:
                flash("企业名称为必填项", "danger")
                return render_template("enterprise_form.html", 模式="new", 企业=None)

            db.session.add(企业)
            db.session.flush()
            if 外贸负责人:
                db.session.add(
                    Contact(
                        enterprise_id=企业.id,
                        contact_type="外贸负责人",
                        name=外贸负责人,
                        position="外贸负责人",
                    )
                )
            记录审计日志("新增企业", "enterprise", target_id=企业.id, detail=企业.company_name)
            db.session.commit()
            flash(f"企业 {企业.company_name} 新增成功", "success")
            return redirect(url_for("enterprise_detail", id=企业.id))

        return render_template("enterprise_form.html", 模式="new", 企业=None)

    @app.route("/enterprises/<int:id>")
    def enterprise_detail(id):
        企业 = Enterprise.query.get_or_404(id)
        联系人列表 = Contact.query.filter_by(enterprise_id=id).all()
        产品列表 = Product.query.filter_by(enterprise_id=id).all()
        资质列表 = Qualification.query.filter_by(enterprise_id=id).order_by(
            Qualification.expiry_date.is_(None), Qualification.expiry_date.asc()
        ).all()
        资质展示列表 = [构建证照展示项(资质) for 资质 in 资质列表]
        文件列表 = Document.query.filter_by(enterprise_id=id).all()

        return render_template(
            "enterprise_detail.html",
            企业=企业,
            联系人列表=联系人列表,
            产品列表=产品列表,
            资质列表=资质列表,
            资质展示列表=资质展示列表,
            文件列表=文件列表,
        )

    @app.route("/enterprises/<int:id>/analysis-note", methods=["POST"])
    def enterprise_analysis_note_save(id):
        企业 = Enterprise.query.get_or_404(id)
        备注内容 = request.form.get("analysis_note", "").strip() or None
        分析备注 = EnterpriseAnalysisNote.query.filter_by(enterprise_id=id).first()
        if 分析备注:
            分析备注.note = 备注内容
            分析备注.updated_at = datetime.utcnow()
        else:
            分析备注 = EnterpriseAnalysisNote(enterprise_id=企业.id, note=备注内容)
            db.session.add(分析备注)
        db.session.commit()
        flash("出海方案分析备注已保存。", "success")
        return redirect(url_for("enterprise_detail", id=企业.id))

    @app.route("/enterprises/<int:id>/edit", methods=["GET", "POST"])
    def enterprise_edit(id):
        企业 = Enterprise.query.get_or_404(id)
        外贸联系人 = Contact.query.filter_by(enterprise_id=id, contact_type="外贸负责人").first()

        if request.method == "POST":
            企业.company_name = request.form.get("company_name", "").strip()
            企业.english_name = request.form.get("english_name", "").strip() or None
            企业.unified_social_credit_code = request.form.get("unified_social_credit_code", "").strip() or None
            企业.founded_date = 读取日期(request.form.get("founded_date"))
            企业.registered_capital = request.form.get("registered_capital", "").strip() or None
            企业.registered_address = request.form.get("registered_address", "").strip() or None
            企业.business_address = request.form.get("business_address", "").strip() or None
            企业.province = request.form.get("province", "").strip() or None
            企业.city = request.form.get("city", "").strip() or None
            企业.district = request.form.get("district", "").strip() or None
            企业.company_type = request.form.get("company_type", "").strip() or None
            企业.industry_code = request.form.get("industry_code", "").strip() or None
            企业.industry_category = request.form.get("industry_category", "").strip() or None
            企业.sub_industry = request.form.get("sub_industry", "").strip() or None
            企业.main_products = request.form.get("main_products", "").strip() or None
            企业.main_business = request.form.get("main_business", "").strip() or None
            企业.is_manufacturer = 读取布尔(request.form, "is_manufacturer")
            企业.is_trader = 读取布尔(request.form, "is_trader")
            企业.is_brand_owner = 读取布尔(request.form, "is_brand_owner")
            企业.is_oem_odm = 读取布尔(request.form, "is_oem_odm")
            企业.is_service_provider = 读取布尔(request.form, "is_service_provider")
            企业.is_high_tech = 读取布尔(request.form, "is_high_tech")
            企业.is_specialized_new = 读取布尔(request.form, "is_specialized_new")
            企业.is_listed_or_pre_ipo = 读取布尔(request.form, "is_listed_or_pre_ipo")
            企业.has_foreign_trade_experience = 读取布尔(request.form, "has_foreign_trade_experience")
            企业.export_countries = request.form.get("export_countries", "").strip() or None
            企业.target_markets = request.form.get("target_markets", "").strip() or None
            企业.annual_capacity = request.form.get("annual_capacity", "").strip() or None
            企业.employee_count = 读取整数(request.form.get("employee_count"))
            企业.factory_area = request.form.get("factory_area", "").strip() or None
            企业.main_equipment = request.form.get("main_equipment", "").strip() or None
            企业.annual_revenue = 读取金额(request.form.get("annual_revenue"))
            企业.export_revenue = 读取金额(request.form.get("export_revenue"))
            企业.service_needs = request.form.get("service_needs", "").strip() or None
            企业.risk_notes = request.form.get("risk_notes", "").strip() or None
            企业.status = request.form.get("status", "草稿").strip() or "草稿"
            企业.project_owner = request.form.get("project_owner", "").strip() or None
            企业.updated_at = datetime.utcnow()

            外贸负责人 = request.form.get("trade_owner", "").strip()
            if 外贸负责人 and not 外贸联系人:
                外贸联系人 = Contact(
                    enterprise_id=企业.id,
                    contact_type="外贸负责人",
                    name=外贸负责人,
                    position="外贸负责人",
                )
                db.session.add(外贸联系人)
            elif 外贸联系人:
                if 外贸负责人:
                    外贸联系人.name = 外贸负责人
                else:
                    db.session.delete(外贸联系人)

            if not 企业.company_name:
                flash("企业名称为必填项", "danger")
                return render_template("enterprise_form.html", 模式="edit", 企业=企业, 外贸负责人=外贸负责人)

            记录审计日志("编辑企业", "enterprise", target_id=企业.id, detail=企业.company_name)
            db.session.commit()
            flash("企业信息更新成功", "success")
            return redirect(url_for("enterprise_detail", id=企业.id))

        return render_template(
            "enterprise_form.html",
            模式="edit",
            企业=企业,
            外贸负责人=外贸联系人.name if 外贸联系人 else "",
        )

    @app.route("/enterprises/<int:id>/delete", methods=["POST"])
    @admin_required
    def enterprise_delete(id):
        企业 = Enterprise.query.get_or_404(id)
        if request.form.get("confirm_delete") != "YES":
            flash("请勾选二次确认后再删除企业。", "warning")
            return redirect(url_for("enterprise_list"))
        if Product.query.filter_by(enterprise_id=企业.id).count() > 0 or ProjectProgress.query.filter_by(enterprise_id=企业.id).count() > 0:
            企业.status = "停用"
            记录审计日志("编辑企业", "enterprise", target_id=企业.id, detail=f"{企业.company_name} 标记为停用")
            db.session.commit()
            flash("企业存在产品或项目进展，已自动标记为停用。", "warning")
            return redirect(url_for("enterprise_detail", id=企业.id))
        记录审计日志("删除企业", "enterprise", target_id=企业.id, detail=企业.company_name)
        db.session.delete(企业)
        db.session.commit()
        flash("企业已删除", "success")
        return redirect(url_for("enterprise_list"))

    @app.route("/qualifications")
    def qualification_list():
        证书状态 = request.args.get("status", "", type=str).strip()
        查询 = Qualification.query.join(Enterprise, Qualification.enterprise_id == Enterprise.id).outerjoin(
            Product, Qualification.product_id == Product.id
        )

        if 证书状态:
            当前日期 = date.today()
            if 证书状态 == "未填写":
                查询 = 查询.filter(Qualification.expiry_date.is_(None))
            elif 证书状态 == "已过期":
                查询 = 查询.filter(Qualification.expiry_date.isnot(None), Qualification.expiry_date < 当前日期)

        证照列表 = 查询.order_by(
            Qualification.expiry_date.is_(None), Qualification.expiry_date.asc(), Qualification.id.desc()
        ).all()
        证照展示列表 = [构建证照展示项(资质) for 资质 in 证照列表]
        if 证书状态 == "即将到期":
            证照展示列表 = [项 for 项 in 证照展示列表 if 项["证书状态"] == "即将到期"]
        elif 证书状态 == "正常":
            证照展示列表 = [项 for 项 in 证照展示列表 if 项["证书状态"] == "正常"]

        return render_template(
            "qualifications/list.html",
            证照展示列表=证照展示列表,
            当前状态=证书状态,
            状态选项=["", "未填写", "已过期", "即将到期", "正常"],
        )

    @app.route("/qualifications/new", methods=["GET", "POST"])
    def qualification_new():
        企业列表 = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        证书类型选项 = 获取证书类型选项()

        if request.method == "POST":
            enterprise_id = request.form.get("enterprise_id", type=int)
            企业 = Enterprise.query.get(enterprise_id) if enterprise_id else None
            if not 企业:
                flash("请选择有效企业。", "danger")
                return render_template(
                    "qualifications/form.html",
                    企业列表=企业列表,
                    产品列表=[],
                    证书类型选项=证书类型选项,
                    表单=request.form,
                )

            product_id = request.form.get("product_id", type=int)
            产品 = Product.query.filter_by(id=product_id, enterprise_id=enterprise_id).first() if product_id else None
            if product_id and not 产品:
                flash("请选择该企业下的有效产品。", "danger")
                return render_template(
                    "qualifications/form.html",
                    企业列表=企业列表,
                    产品列表=Product.query.filter_by(enterprise_id=enterprise_id).order_by(Product.product_name_cn.asc()).all(),
                    证书类型选项=证书类型选项,
                    表单=request.form,
                )

            资质 = Qualification(
                enterprise_id=enterprise_id,
                product_id=产品.id if 产品 else None,
                certificate_name=request.form.get("certificate_name", "").strip(),
                certificate_type=request.form.get("certificate_type", "").strip() or None,
                certificate_no=request.form.get("certificate_no", "").strip() or None,
                covered_products=request.form.get("covered_products", "").strip() or None,
                issuing_authority=request.form.get("issuing_authority", "").strip() or None,
                issue_date=读取日期(request.form.get("issue_date")),
                expiry_date=读取日期(request.form.get("expiry_date")),
                status=计算证书状态(读取日期(request.form.get("expiry_date"))),
                affects_recommendation=读取布尔(request.form, "affects_recommendation"),
                file_path=request.form.get("file_path", "").strip() or None,
                notes=request.form.get("notes", "").strip() or None,
            )
            if not 资质.certificate_name:
                flash("证书名称为必填项。", "danger")
                return render_template(
                    "qualifications/form.html",
                    企业列表=企业列表,
                    产品列表=Product.query.filter_by(enterprise_id=enterprise_id).order_by(Product.product_name_cn.asc()).all(),
                    证书类型选项=证书类型选项,
                    表单=request.form,
                )

            db.session.add(资质)
            db.session.commit()
            flash("资质证照新增成功。", "success")
            return redirect(url_for("qualification_list"))

        默认企业 = request.args.get("enterprise_id", type=int)
        产品列表 = Product.query.filter_by(enterprise_id=默认企业).order_by(Product.product_name_cn.asc()).all() if 默认企业 else []
        return render_template(
            "qualifications/form.html",
            企业列表=企业列表,
            产品列表=产品列表,
            证书类型选项=证书类型选项,
            表单={},
        )

    @app.post("/qualifications/<int:id>/delete")
    def qualification_delete(id):
        资质 = Qualification.query.get_or_404(id)
        db.session.delete(资质)
        db.session.commit()
        flash("证照记录已删除。", "info")
        return redirect(url_for("qualification_list"))

    @app.route("/登录", methods=["GET", "POST"])
    def 登录():
        if session.get("用户"):
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            用户名 = request.form.get("用户名", "").strip()
            密码 = request.form.get("密码", "").strip()

            用户 = User.query.filter_by(username=用户名).first()
            if 用户 and check_password_hash(用户.password, 密码):
                session["用户"] = 用户.username
                session["角色"] = 用户.role
                flash("登录成功", "success")
                return redirect(url_for("dashboard"))

            flash("用户名或密码错误", "danger")

        return render_template("login.html")

    @app.route("/退出")
    def 退出():
        session.pop("用户", None)
        session.pop("角色", None)
        flash("已退出登录", "info")
        return redirect(url_for("登录"))

    @app.route("/products")
    def product_list():
        q_enterprise = request.args.get("enterprise", "").strip()
        q_keyword = request.args.get("keyword", "").strip()
        q_category = request.args.get("category", "").strip()
        q_hs_code = request.args.get("hs_code", "").strip()
        q_target_market = request.args.get("target_market", "").strip()
        q_certification = request.args.get("certification", "").strip()
        q_price_min = request.args.get("price_min", "").strip()
        q_price_max = request.args.get("price_max", "").strip()

        query = Product.query.join(Enterprise, Product.enterprise_id == Enterprise.id)

        if q_enterprise:
            query = query.filter(Enterprise.company_name.ilike(f"%{q_enterprise}%"))
        if q_keyword:
            keyword_like = f"%{q_keyword}%"
            query = query.filter(
                or_(
                    Product.product_name_cn.ilike(keyword_like),
                    Product.product_name_en.ilike(keyword_like),
                    Product.model.ilike(keyword_like),
                )
            )
        if q_category:
            query = query.filter(Product.product_category.ilike(f"%{q_category}%"))
        if q_hs_code:
            query = query.filter(Product.hs_code.ilike(f"%{q_hs_code}%"))
        if q_target_market:
            query = query.filter(Product.target_market.ilike(f"%{q_target_market}%"))
        if q_certification:
            query = query.filter(Product.certifications.ilike(f"%{q_certification}%"))

        if q_price_min:
            try:
                price_min = Decimal(q_price_min)
                query = query.filter(or_(Product.fob_price >= price_min, Product.cif_price >= price_min, Product.ddp_price >= price_min))
            except InvalidOperation:
                flash("最低价格输入格式无效，已忽略。", "warning")
        if q_price_max:
            try:
                price_max = Decimal(q_price_max)
                query = query.filter(or_(Product.fob_price <= price_max, Product.cif_price <= price_max, Product.ddp_price <= price_max))
            except InvalidOperation:
                flash("最高价格输入格式无效，已忽略。", "warning")

        products = query.order_by(Product.updated_at.desc()).all()
        enterprises = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        categories = [r[0] for r in db.session.query(Product.product_category).filter(Product.product_category.isnot(None)).distinct().all()]
        return render_template(
            "products/list.html",
            products=products,
            enterprises=enterprises,
            categories=categories,
            filters=request.args,
        )

    @app.route("/products/new", methods=["GET", "POST"])
    def product_new():
        enterprises = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        if request.method == "POST":
            enterprise_id = request.form.get("enterprise_id", type=int)
            enterprise = Enterprise.query.get(enterprise_id) if enterprise_id else None
            if not enterprise:
                flash("请选择有效的所属企业。", "danger")
                return render_template(
                    "products/form.html",
                    form_action=url_for("product_new"),
                    enterprises=enterprises,
                    form_title="新增产品",
                    sections=PRODUCT_FORM_SECTIONS,
                    product=None,
                )

            product = Product(
                enterprise_id=enterprise.id,
                product_code=generate_product_code(enterprise.id),
            )
            try:
                fill_product_from_form(product, request.form)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template(
                    "products/form.html",
                    form_action=url_for("product_new"),
                    enterprises=enterprises,
                    form_title="新增产品",
                    sections=PRODUCT_FORM_SECTIONS,
                    product=product,
                )
            db.session.add(product)
            db.session.flush()
            记录审计日志("新增产品", "product", target_id=product.id, detail=product.product_name_cn)
            db.session.commit()
            flash(f"产品已创建，编号：{product.product_code}。", "success")
            return redirect(url_for("product_detail", product_id=product.id))

        return render_template(
            "products/form.html",
            form_action=url_for("product_new"),
            enterprises=enterprises,
            form_title="新增产品",
            sections=PRODUCT_FORM_SECTIONS,
            product=None,
        )

    @app.route("/products/<int:product_id>")
    def product_detail(product_id):
        product = Product.query.get_or_404(product_id)
        enterprise = Enterprise.query.get(product.enterprise_id)
        certificates = Qualification.query.filter_by(product_id=product.id).order_by(Qualification.expiry_date.desc()).all()
        product_files = Document.query.filter_by(product_id=product.id).order_by(Document.uploaded_at.desc()).all()
        匹配记录 = (
            MatchRecord.query.filter_by(product_id=product.id)
            .order_by(MatchRecord.match_score.desc(), MatchRecord.updated_at.desc())
            .all()
        )
        匹配需求列表 = [
            {
                "记录": 记录,
                "需求": Demand.query.get(记录.demand_id),
            }
            for 记录 in 匹配记录
        ]
        archive_code = f"{enterprise.enterprise_code}_{product.product_code}" if enterprise else product.product_code
        return render_template(
            "products/detail.html",
            product=product,
            enterprise=enterprise,
            certificates=certificates,
            product_files=product_files,
            archive_code=archive_code,
            匹配需求列表=匹配需求列表,
        )

    @app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
    def product_edit(product_id):
        product = Product.query.get_or_404(product_id)
        enterprises = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        if request.method == "POST":
            enterprise_id = request.form.get("enterprise_id", type=int)
            enterprise = Enterprise.query.get(enterprise_id) if enterprise_id else None
            if not enterprise:
                flash("请选择有效的所属企业。", "danger")
                return render_template(
                    "products/form.html",
                    form_action=url_for("product_edit", product_id=product.id),
                    enterprises=enterprises,
                    form_title="编辑产品",
                    sections=PRODUCT_FORM_SECTIONS,
                    product=product,
                )

            old_enterprise_id = product.enterprise_id
            product.enterprise_id = enterprise.id
            if old_enterprise_id != enterprise.id:
                product.product_code = generate_product_code(enterprise.id)
            try:
                fill_product_from_form(product, request.form)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template(
                    "products/form.html",
                    form_action=url_for("product_edit", product_id=product.id),
                    enterprises=enterprises,
                    form_title="编辑产品",
                    sections=PRODUCT_FORM_SECTIONS,
                    product=product,
                )
            记录审计日志("编辑产品", "product", target_id=product.id, detail=product.product_name_cn)
            db.session.commit()
            flash("产品信息已更新。", "success")
            return redirect(url_for("product_detail", product_id=product.id))

        return render_template(
            "products/form.html",
            form_action=url_for("product_edit", product_id=product.id),
            enterprises=enterprises,
            form_title="编辑产品",
            sections=PRODUCT_FORM_SECTIONS,
            product=product,
        )

    @app.post("/products/<int:product_id>/delete")
    @admin_required
    def product_delete(product_id):
        product = Product.query.get_or_404(product_id)
        if request.form.get("confirm_delete") != "YES":
            flash("请勾选二次确认后再删除产品。", "warning")
            return redirect(url_for("product_list"))
        if ProjectProgress.query.filter_by(product_id=product.id).count() > 0:
            flash("该产品存在项目进展，暂不允许直接删除。", "danger")
            return redirect(url_for("product_detail", product_id=product.id))
        记录审计日志("删除产品", "product", target_id=product.id, detail=product.product_name_cn)
        db.session.delete(product)
        db.session.commit()
        flash("产品已删除。", "info")
        return redirect(url_for("product_list"))

    @app.route("/projects")
    def project_list():
        current_stage = request.args.get("current_stage", "", type=str).strip()
        project_owner = request.args.get("project_owner", "", type=str).strip()
        foreign_client = request.args.get("foreign_client", "", type=str).strip()
        enterprise_name = request.args.get("enterprise_name", "", type=str).strip()

        query = ProjectProgress.query
        if current_stage:
            query = query.filter(ProjectProgress.current_stage == current_stage)
        if project_owner:
            query = query.filter(ProjectProgress.project_owner == project_owner)
        if foreign_client:
            query = query.join(ForeignClient, ProjectProgress.foreign_client_id == ForeignClient.id).filter(
                ForeignClient.client_name.ilike(f"%{foreign_client}%")
            )
        if enterprise_name:
            query = query.join(Enterprise, ProjectProgress.enterprise_id == Enterprise.id).filter(
                Enterprise.company_name.ilike(f"%{enterprise_name}%")
            )

        projects = query.order_by(ProjectProgress.updated_at.desc(), ProjectProgress.id.desc()).all()
        enterprise_map = {item.id: item for item in Enterprise.query.filter(Enterprise.id.in_({p.enterprise_id for p in projects if p.enterprise_id})).all()} if projects else {}
        product_map = {item.id: item for item in Product.query.filter(Product.id.in_({p.product_id for p in projects if p.product_id})).all()} if projects else {}
        client_map = {item.id: item for item in ForeignClient.query.filter(ForeignClient.id.in_({p.foreign_client_id for p in projects if p.foreign_client_id})).all()} if projects else {}

        owners = [
            row[0]
            for row in db.session.query(ProjectProgress.project_owner)
            .filter(ProjectProgress.project_owner.isnot(None), ProjectProgress.project_owner != "")
            .distinct()
            .order_by(ProjectProgress.project_owner)
            .all()
        ]

        return render_template(
            "projects/list.html",
            projects=projects,
            enterprise_map=enterprise_map,
            product_map=product_map,
            client_map=client_map,
            filters={
                "current_stage": current_stage,
                "project_owner": project_owner,
                "foreign_client": foreign_client,
                "enterprise_name": enterprise_name,
            },
            stage_options=PROJECT_STAGE_OPTIONS,
            owner_options=owners,
            project_code=项目编号,
        )

    @app.route("/projects/new", methods=["GET", "POST"])
    def project_new():
        enterprises = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        products = Product.query.order_by(Product.product_name_cn.asc()).all()
        clients = ForeignClient.query.order_by(ForeignClient.client_name.asc()).all()
        demands = Demand.query.order_by(Demand.updated_at.desc()).all()

        if request.method == "POST":
            project = ProjectProgress()
            填充项目字段(project, request.form)
            if not project.enterprise_id:
                flash("请选择企业。", "danger")
                return render_template(
                    "projects/form.html",
                    form_title="新增撮合项目",
                    enterprises=enterprises,
                    products=products,
                    clients=clients,
                    demands=demands,
                    stage_options=PROJECT_STAGE_OPTIONS,
                    sample_status_options=SAMPLE_STATUS_OPTIONS,
                    quotation_status_options=QUOTATION_STATUS_OPTIONS,
                    contract_status_options=CONTRACT_STATUS_OPTIONS,
                    form_data=request.form,
                )

            db.session.add(project)
            db.session.commit()
            flash(f"项目 {项目编号(project)} 创建成功。", "success")
            return redirect(url_for("project_detail", project_id=project.id))

        return render_template(
            "projects/form.html",
            form_title="新增撮合项目",
            enterprises=enterprises,
            products=products,
            clients=clients,
            demands=demands,
            stage_options=PROJECT_STAGE_OPTIONS,
            sample_status_options=SAMPLE_STATUS_OPTIONS,
            quotation_status_options=QUOTATION_STATUS_OPTIONS,
            contract_status_options=CONTRACT_STATUS_OPTIONS,
            form_data={},
        )

    @app.route("/projects/<int:project_id>")
    def project_detail(project_id):
        project = ProjectProgress.query.get_or_404(project_id)
        enterprise = Enterprise.query.get(project.enterprise_id) if project.enterprise_id else None
        product = Product.query.get(project.product_id) if project.product_id else None
        client = ForeignClient.query.get(project.foreign_client_id) if project.foreign_client_id else None
        demand = Demand.query.get(project.demand_id) if project.demand_id else None
        documents = Document.query.filter_by(related_project_id=project.id).order_by(Document.uploaded_at.desc()).all()
        timeline = 构建项目时间线(project)

        return render_template(
            "projects/detail.html",
            project=project,
            enterprise=enterprise,
            product=product,
            client=client,
            demand=demand,
            documents=documents,
            timeline=timeline,
            project_code=项目编号(project),
        )

    @app.route("/documents")
    def document_list():
        enterprise_id = request.args.get("enterprise_id", type=int)
        product_id = request.args.get("product_id", type=int)
        document_type = request.args.get("document_type", "", type=str).strip()
        upload_date = request.args.get("upload_date", "", type=str).strip()
        keyword = request.args.get("keyword", "", type=str).strip()

        query = Document.query
        if enterprise_id:
            query = query.filter(Document.enterprise_id == enterprise_id)
        if product_id:
            query = query.filter(Document.product_id == product_id)
        if document_type:
            query = query.filter(Document.document_type == document_type)
        if upload_date:
            日期 = 读取日期(upload_date)
            if 日期:
                query = query.filter(db.func.date(Document.uploaded_at) == 日期)
            else:
                flash("上传日期格式无效，已忽略该筛选。", "warning")
        if keyword:
            query = query.filter(Document.document_name.ilike(f"%{keyword}%"))

        documents = query.order_by(Document.uploaded_at.desc(), Document.id.desc()).all()
        enterprises = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        products = Product.query.filter_by(enterprise_id=enterprise_id).order_by(Product.product_name_cn.asc()).all() if enterprise_id else Product.query.order_by(Product.product_name_cn.asc()).all()
        enterprise_map = {item.id: item for item in Enterprise.query.filter(Enterprise.id.in_({d.enterprise_id for d in documents if d.enterprise_id})).all()} if documents else {}
        product_map = {item.id: item for item in Product.query.filter(Product.id.in_({d.product_id for d in documents if d.product_id})).all()} if documents else {}

        return render_template(
            "documents/list.html",
            documents=documents,
            enterprises=enterprises,
            products=products,
            enterprise_map=enterprise_map,
            product_map=product_map,
            filters={
                "enterprise_id": enterprise_id,
                "product_id": product_id,
                "document_type": document_type,
                "upload_date": upload_date,
                "keyword": keyword,
            },
            document_types=DOCUMENT_TYPE_OPTIONS,
        )

    @app.route("/documents/upload", methods=["GET", "POST"])
    def document_upload():
        enterprises = Enterprise.query.order_by(Enterprise.company_name.asc()).all()
        projects = ProjectProgress.query.order_by(ProjectProgress.updated_at.desc()).all()

        if request.method == "POST":
            enterprise_id = request.form.get("enterprise_id", type=int)
            enterprise = Enterprise.query.get(enterprise_id) if enterprise_id else None
            if not enterprise:
                flash("所属企业为必填项。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=[],
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )

            product_id = request.form.get("product_id", type=int)
            product = Product.query.filter_by(id=product_id, enterprise_id=enterprise.id).first() if product_id else None
            if product_id and not product:
                flash("所属产品不属于当前企业，请重新选择。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )

            document_type = request.form.get("document_type", "").strip().upper()
            document_name = request.form.get("document_name", "").strip()
            version = request.form.get("version", "").strip() or "V01"
            uploaded_by = request.form.get("uploaded_by", "").strip() or "未署名"
            notes = request.form.get("notes", "").strip() or None
            related_project_id = request.form.get("related_project_id", type=int)

            if not document_type:
                flash("文件类型为必填项。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )
            if document_type not in {code for code, _ in DOCUMENT_TYPE_OPTIONS}:
                flash("文件类型不在允许范围内。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )
            if not document_name:
                flash("文件名称为必填项。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )
            if 包含非法文件名字符(document_name):
                flash("文件名称不能包含以下字符：\\ / : * ? \" < > |", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )

            上传文件 = request.files.get("file")
            if not 上传文件 or not 上传文件.filename:
                flash("请选择需要上传的文件。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )

            扩展名 = Path(上传文件.filename).suffix.lower()
            if 扩展名 in BLOCKED_EXTENSIONS or 扩展名 not in ALLOWED_EXTENSIONS:
                flash("文件类型不允许上传。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )
            if request.content_length and request.content_length > MAX_UPLOAD_SIZE:
                flash("单文件大小不能超过 100MB。", "danger")
                return render_template(
                    "documents/upload.html",
                    enterprises=enterprises,
                    products=Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.product_name_cn.asc()).all(),
                    projects=projects,
                    document_types=DOCUMENT_TYPE_OPTIONS,
                    form_data=request.form,
                )

            安全原始文件名 = secure_filename(上传文件.filename)
            if not 安全原始文件名:
                flash("上传文件名无效，请重命名后重试。", "danger")
                return redirect(url_for("document_upload"))

            企业目录 = app.config["UPLOAD_ROOT"] / f"{enterprise.enterprise_code}_{清洗路径片段(enterprise.company_name)}"
            if product:
                归档目录 = 企业目录 / "05_产品资料" / f"{enterprise.enterprise_code}_{product.product_code}_{清洗路径片段(product.product_name_cn)}"
            else:
                归档目录 = 企业目录 / 获取文件分类目录(document_type)
            归档目录.mkdir(parents=True, exist_ok=True)

            日期文本 = datetime.now().strftime("%Y%m%d")
            标准文件名 = 构建标准文件名(
                enterprise_code=enterprise.enterprise_code,
                product_code=product.product_code if product else None,
                document_type=document_type,
                document_name=document_name,
                version=version,
                date_text=日期文本,
                uploaded_by=uploaded_by,
                extension=扩展名,
            )
            存储路径 = 生成不覆盖文件路径(归档目录 / 标准文件名)
            上传文件.save(存储路径)

            document = Document(
                enterprise_id=enterprise.id,
                product_id=product.id if product else None,
                related_project_id=related_project_id,
                document_type=document_type,
                document_name=document_name,
                version=version,
                file_path=str(存储路径.relative_to(BASE_DIR)),
                original_filename=安全原始文件名,
                uploaded_by=uploaded_by,
                notes=notes,
            )
            db.session.add(document)
            db.session.flush()
            记录审计日志("上传文件", "document", target_id=document.id, detail=document.document_name)
            db.session.commit()
            flash("文件上传并归档成功。", "success")
            return redirect(url_for("document_list"))

        default_enterprise_id = request.args.get("enterprise_id", type=int)
        default_product_id = request.args.get("product_id", type=int)
        products = Product.query.filter_by(enterprise_id=default_enterprise_id).order_by(Product.product_name_cn.asc()).all() if default_enterprise_id else []
        return render_template(
            "documents/upload.html",
            enterprises=enterprises,
            products=products,
            projects=projects,
            document_types=DOCUMENT_TYPE_OPTIONS,
            form_data={
                "enterprise_id": default_enterprise_id,
                "product_id": default_product_id,
            } if default_enterprise_id else {},
        )

    @app.route("/documents/<int:document_id>/download")
    def document_download(document_id):
        document = Document.query.get_or_404(document_id)
        文件路径 = BASE_DIR / document.file_path
        if not 文件路径.exists():
            flash("文件不存在，可能已被移动或删除。", "danger")
            return redirect(url_for("document_list"))
        return send_from_directory(
            文件路径.parent,
            文件路径.name,
            as_attachment=True,
            download_name=document.original_filename or 文件路径.name,
        )

    @app.post("/documents/<int:document_id>/delete")
    @admin_required
    def document_delete(document_id):
        document = Document.query.get_or_404(document_id)
        if request.form.get("confirm_delete") != "YES":
            flash("请勾选二次确认后再删除文件。", "warning")
            return redirect(url_for("document_list"))
        文件路径 = BASE_DIR / document.file_path
        if 文件路径.exists() and 文件路径.is_file():
            文件路径.unlink()
        记录审计日志("删除文件", "document", target_id=document.id, detail=document.document_name)
        db.session.delete(document)
        db.session.commit()
        flash("文件已删除。", "success")
        return redirect(url_for("document_list"))

    @app.route("/foreign-clients")
    def foreign_client_list():
        q = request.args.get("q", "", type=str).strip()
        国家地区 = request.args.get("country_region", "", type=str).strip()
        query = ForeignClient.query
        if q:
            query = query.filter(
                or_(
                    ForeignClient.client_name.ilike(f"%{q}%"),
                    ForeignClient.contact_name.ilike(f"%{q}%"),
                    ForeignClient.contact_email.ilike(f"%{q}%"),
                )
            )
        if 国家地区:
            query = query.filter(ForeignClient.country_region == 国家地区)
        clients = query.order_by(ForeignClient.updated_at.desc()).all()
        国家地区列表 = [
            row[0]
            for row in db.session.query(ForeignClient.country_region)
            .filter(ForeignClient.country_region.isnot(None), ForeignClient.country_region != "")
            .distinct()
            .order_by(ForeignClient.country_region)
            .all()
        ]
        return render_template(
            "foreign_clients/list.html",
            clients=clients,
            filters={"q": q, "country_region": 国家地区},
            国家地区列表=国家地区列表,
        )

    @app.route("/foreign-clients/new", methods=["GET", "POST"])
    def foreign_client_new():
        if request.method == "POST":
            client = ForeignClient()
            填充外资客户字段(client, request.form)
            if not client.client_name:
                flash("客户名称为必填项。", "danger")
                return render_template("foreign_clients/form.html", client=client, form_title="新增外资客户")
            db.session.add(client)
            db.session.commit()
            flash("外资客户创建成功。", "success")
            return redirect(url_for("foreign_client_detail", client_id=client.id))
        return render_template("foreign_clients/form.html", client=None, form_title="新增外资客户")

    @app.route("/foreign-clients/<int:client_id>")
    def foreign_client_detail(client_id):
        client = ForeignClient.query.get_or_404(client_id)
        demands = Demand.query.filter_by(foreign_client_id=client.id).order_by(Demand.updated_at.desc()).all()
        return render_template("foreign_clients/detail.html", client=client, demands=demands)

    @app.route("/foreign-clients/<int:client_id>/edit", methods=["GET", "POST"])
    def foreign_client_edit(client_id):
        client = ForeignClient.query.get_or_404(client_id)
        if request.method == "POST":
            填充外资客户字段(client, request.form)
            if not client.client_name:
                flash("客户名称为必填项。", "danger")
                return render_template("foreign_clients/form.html", client=client, form_title="编辑外资客户")
            db.session.commit()
            flash("外资客户更新成功。", "success")
            return redirect(url_for("foreign_client_detail", client_id=client.id))
        return render_template("foreign_clients/form.html", client=client, form_title="编辑外资客户")

    @app.route("/demands")
    def demand_list():
        status = request.args.get("status", "", type=str).strip()
        client_id = request.args.get("foreign_client_id", type=int)
        keyword = request.args.get("keyword", "", type=str).strip()
        query = Demand.query
        if status:
            query = query.filter(Demand.status == status)
        if client_id:
            query = query.filter(Demand.foreign_client_id == client_id)
        if keyword:
            query = query.filter(
                or_(
                    Demand.demand_code.ilike(f"%{keyword}%"),
                    Demand.purchase_category.ilike(f"%{keyword}%"),
                    Demand.product_keywords.ilike(f"%{keyword}%"),
                )
            )
        demands = query.order_by(Demand.updated_at.desc()).all()
        clients = ForeignClient.query.order_by(ForeignClient.client_name.asc()).all()
        status_options = [
            row[0]
            for row in db.session.query(Demand.status)
            .filter(Demand.status.isnot(None), Demand.status != "")
            .distinct()
            .order_by(Demand.status)
            .all()
        ]
        client_map = {client.id: client for client in clients}
        return render_template(
            "demands/list.html",
            demands=demands,
            clients=clients,
            client_map=client_map,
            filters={"status": status, "foreign_client_id": client_id, "keyword": keyword},
            status_options=status_options,
        )

    @app.route("/demands/new", methods=["GET", "POST"])
    def demand_new():
        clients = ForeignClient.query.order_by(ForeignClient.client_name.asc()).all()
        if request.method == "POST":
            demand = Demand(demand_code=生成需求编号())
            填充需求字段(demand, request.form)
            if not demand.foreign_client_id:
                flash("请选择外资客户。", "danger")
                return render_template("demands/form.html", demand=demand, clients=clients, form_title="新增外资需求")
            db.session.add(demand)
            db.session.commit()
            flash(f"需求创建成功，编号：{demand.demand_code}。", "success")
            return redirect(url_for("demand_detail", demand_id=demand.id))

        draft = Demand(demand_code=生成需求编号())
        return render_template("demands/form.html", demand=draft, clients=clients, form_title="新增外资需求")

    @app.route("/demands/<int:demand_id>")
    def demand_detail(demand_id):
        demand = Demand.query.get_or_404(demand_id)
        client = ForeignClient.query.get(demand.foreign_client_id)
        匹配记录 = (
            MatchRecord.query.filter_by(demand_id=demand.id)
            .order_by(MatchRecord.match_score.desc(), MatchRecord.updated_at.desc())
            .all()
        )
        匹配结果 = [
            {
                "记录": 记录,
                "企业": Enterprise.query.get(记录.enterprise_id),
                "产品": Product.query.get(记录.product_id) if 记录.product_id else None,
            }
            for 记录 in 匹配记录
        ]
        return render_template("demands/detail.html", demand=demand, client=client, 匹配结果=匹配结果)

    @app.post("/demands/<int:demand_id>/generate-matches")
    def generate_demand_matches(demand_id):
        demand = Demand.query.get_or_404(demand_id)
        MatchRecord.query.filter_by(demand_id=demand.id).delete()
        products = Product.query.order_by(Product.updated_at.desc()).all()
        for product in products:
            enterprise = Enterprise.query.get(product.enterprise_id)
            if not enterprise:
                continue
            score, reasons, risks = 计算匹配得分(demand, product, enterprise)
            status = 计算推荐状态(score)
            记录 = MatchRecord(
                demand_id=demand.id,
                enterprise_id=enterprise.id,
                product_id=product.id,
                match_score=Decimal(score),
                match_reason="；".join(reasons) if reasons else "暂无明显匹配点",
                risk_notes="；".join(risks) if risks else "未发现显著风险",
                recommendation_status=status,
            )
            db.session.add(记录)
        db.session.commit()
        flash("匹配结果已生成。", "success")
        return redirect(url_for("demand_detail", demand_id=demand.id))

    @app.cli.command("init-db")
    def init_db_command():
        """初始化数据库（可选：flask init-db）。"""

        init_db(app)

    return app


def 生成企业编号():
    最新企业 = Enterprise.query.order_by(Enterprise.id.desc()).first()
    if not 最新企业:
        return "E001"

    最新编号 = 最新企业.enterprise_code or "E000"
    try:
        当前数字 = int(最新编号[1:])
    except (ValueError, TypeError):
        当前数字 = Enterprise.query.count()
    return f"E{当前数字 + 1:03d}"


def 获取企业行业分布():
    rows = (
        db.session.query(Enterprise.industry_category, func.count(Enterprise.id))
        .filter(Enterprise.industry_category.isnot(None), Enterprise.industry_category != "")
        .group_by(Enterprise.industry_category)
        .order_by(func.count(Enterprise.id).desc())
        .limit(10)
        .all()
    )
    return {"labels": [row[0] for row in rows], "data": [row[1] for row in rows]}


def 获取产品分类分布():
    rows = (
        db.session.query(Product.product_category, func.count(Product.id))
        .filter(Product.product_category.isnot(None), Product.product_category != "")
        .group_by(Product.product_category)
        .order_by(func.count(Product.id).desc())
        .limit(10)
        .all()
    )
    return {"labels": [row[0] for row in rows], "data": [row[1] for row in rows]}


def 获取项目阶段分布():
    rows = (
        db.session.query(ProjectProgress.current_stage, func.count(ProjectProgress.id))
        .filter(ProjectProgress.current_stage.isnot(None), ProjectProgress.current_stage != "")
        .group_by(ProjectProgress.current_stage)
        .order_by(func.count(ProjectProgress.id).desc())
        .all()
    )
    return {"labels": [row[0] for row in rows], "data": [row[1] for row in rows]}


def 获取最近30天项目趋势():
    today = date.today()
    start = today.fromordinal(today.toordinal() - 29)
    trend_map = {start.fromordinal(start.toordinal() + i): 0 for i in range(30)}
    rows = (
        db.session.query(func.date(ProjectProgress.created_at), func.count(ProjectProgress.id))
        .filter(ProjectProgress.created_at >= datetime.combine(start, datetime.min.time()))
        .group_by(func.date(ProjectProgress.created_at))
        .all()
    )
    for day, count in rows:
        day_value = 读取日期(str(day))
        if day_value in trend_map:
            trend_map[day_value] = count
    labels = [d.strftime("%m-%d") for d in trend_map.keys()]
    data = list(trend_map.values())
    return {"labels": labels, "data": data}


def generate_product_code(enterprise_id):
    最后产品 = Product.query.filter_by(enterprise_id=enterprise_id).order_by(Product.id.desc()).first()
    if not 最后产品:
        return "P001"
    match = re.search(r"(\d+)$", 最后产品.product_code or "")
    seq = int(match.group(1)) + 1 if match else Product.query.filter_by(enterprise_id=enterprise_id).count() + 1
    return f"P{seq:03d}"


def fill_product_from_form(product, form):
    product.product_name_cn = form.get("product_name_cn", "").strip()
    product.product_name_en = form.get("product_name_en", "").strip() or None
    product.product_category = form.get("product_category", "").strip() or None
    product.hs_code = form.get("hs_code", "").strip() or None
    product.model = form.get("model", "").strip() or None
    product.brand = form.get("brand", "").strip() or None
    product.material = form.get("material", "").strip() or None
    product.specification = form.get("specification", "").strip() or None
    product.size = form.get("size", "").strip() or None
    product.weight = form.get("weight", "").strip() or None
    product.color = form.get("color", "").strip() or None
    product.function_description = form.get("function_description", "").strip() or None
    product.application_scenario = form.get("application_scenario", "").strip() or None
    product.unit = form.get("unit", "").strip() or None
    product.moq = form.get("moq", "").strip() or None
    product.production_cycle = form.get("production_cycle", "").strip() or None
    product.sample_cycle = form.get("sample_cycle", "").strip() or None
    product.monthly_capacity = form.get("monthly_capacity", "").strip() or None
    product.customization_supported = 读取布尔(form, "customization_supported")
    product.currency = form.get("currency", "").strip() or "USD"
    product.exw_price = 读取金额(form.get("exw_price"))
    product.fob_price = 读取金额(form.get("fob_price"))
    product.cif_price = 读取金额(form.get("cif_price"))
    product.ddp_price = 读取金额(form.get("ddp_price"))
    product.quote_date = 读取日期(form.get("quote_date"))
    product.quote_valid_until = 读取日期(form.get("quote_valid_until"))
    product.sample_policy = form.get("sample_policy", "").strip() or None
    product.target_market = form.get("target_market", "").strip() or None
    product.existing_sales_countries = form.get("existing_sales_countries", "").strip() or None
    product.certifications = form.get("certifications", "").strip() or None
    product.packaging = form.get("packaging", "").strip() or None
    product.carton_size = form.get("carton_size", "").strip() or None
    product.gross_weight = form.get("gross_weight", "").strip() or None
    product.net_weight = form.get("net_weight", "").strip() or None
    product.loading_quantity = form.get("loading_quantity", "").strip() or None
    product.warranty = form.get("warranty", "").strip() or None
    product.product_selling_points = form.get("product_selling_points", "").strip() or None
    product.notes = form.get("notes", "").strip() or None
    if not product.product_name_cn:
        raise ValueError("产品中文名为必填项")


def 生成需求编号():
    最新需求 = Demand.query.order_by(Demand.id.desc()).first()
    if not 最新需求:
        return "D001"
    最新编号 = 最新需求.demand_code or "D000"
    try:
        当前数字 = int(最新编号[1:])
    except (ValueError, TypeError):
        当前数字 = Demand.query.count()
    return f"D{当前数字 + 1:03d}"


def 填充外资客户字段(client, form):
    client.client_name = form.get("client_name", "").strip()
    client.country_region = form.get("country_region", "").strip() or None
    client.company_type = form.get("company_type", "").strip() or None
    client.contact_name = form.get("contact_name", "").strip() or None
    client.contact_email = form.get("contact_email", "").strip() or None
    client.contact_phone = form.get("contact_phone", "").strip() or None
    client.notes = form.get("notes", "").strip() or None


def 填充需求字段(demand, form):
    demand.foreign_client_id = form.get("foreign_client_id", type=int)
    demand.purchase_category = form.get("purchase_category", "").strip() or None
    demand.product_keywords = form.get("product_keywords", "").strip() or None
    demand.target_price = 读取金额(form.get("target_price"))
    demand.purchase_quantity = form.get("purchase_quantity", "").strip() or None
    demand.required_certifications = form.get("required_certifications", "").strip() or None
    demand.delivery_requirement = form.get("delivery_requirement", "").strip() or None
    demand.trade_terms = form.get("trade_terms", "").strip() or None
    demand.payment_terms = form.get("payment_terms", "").strip() or None
    demand.target_market = form.get("target_market", "").strip() or None
    demand.priority = form.get("priority", "").strip() or "中"
    demand.status = form.get("status", "").strip() or "待跟进"
    demand.notes = form.get("notes", "").strip() or None


def 构建导出数据(export_key):
    导出映射 = {
        "enterprises": ("企业总表", 导出企业总表),
        "products": ("产品总表", 导出产品总表),
        "qualifications": ("资质有效期管理表", 导出资质表),
        "matches": ("外资需求匹配表", 导出匹配表),
        "projects": ("项目进展跟踪表", 导出项目表),
    }
    if export_key not in 导出映射:
        raise ValueError("unknown export key")
    文件名, 生成函数 = 导出映射[export_key]
    表头, 行数据 = 生成函数()
    return 文件名, 表头, 行数据


def 导出企业总表():
    表头 = ["企业编号", "企业名称", "英文名称", "统一社会信用代码", "行业类别", "主营产品", "已出口国家", "目标市场", "状态", "项目负责人", "更新时间"]
    rows = []
    for item in Enterprise.query.order_by(Enterprise.updated_at.desc()).all():
        rows.append([
            item.enterprise_code,
            item.company_name,
            item.english_name,
            item.unified_social_credit_code,
            item.industry_category,
            item.main_products,
            item.export_countries,
            item.target_markets,
            item.status,
            item.project_owner,
            item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at else "",
        ])
    return 表头, rows


def 导出产品总表():
    表头 = ["产品编号", "企业编号", "企业名称", "产品中文名", "产品英文名", "产品类别", "HS编码", "型号", "FOB价格", "币种", "目标市场", "认证", "更新时间"]
    enterprise_map = {e.id: e for e in Enterprise.query.all()}
    rows = []
    for item in Product.query.order_by(Product.updated_at.desc()).all():
        enterprise = enterprise_map.get(item.enterprise_id)
        rows.append([
            item.product_code,
            enterprise.enterprise_code if enterprise else "",
            enterprise.company_name if enterprise else "",
            item.product_name_cn,
            item.product_name_en,
            item.product_category,
            item.hs_code,
            item.model,
            float(item.fob_price) if item.fob_price is not None else None,
            item.currency,
            item.target_market,
            item.certifications,
            item.updated_at.strftime("%Y-%m-%d %H:%M:%S") if item.updated_at else "",
        ])
    return 表头, rows


def 导出资质表():
    表头 = ["企业编号", "企业名称", "产品编号", "产品名称", "证书名称", "证书编号", "发证机构", "发证日期", "到期日期", "状态", "剩余天数", "影响推荐"]
    enterprise_map = {e.id: e for e in Enterprise.query.all()}
    product_map = {p.id: p for p in Product.query.all()}
    rows = []
    for q in Qualification.query.order_by(Qualification.expiry_date.asc()).all():
        enterprise = enterprise_map.get(q.enterprise_id)
        product = product_map.get(q.product_id)
        剩余天数 = (q.expiry_date - date.today()).days if q.expiry_date else None
        rows.append([
            enterprise.enterprise_code if enterprise else "",
            enterprise.company_name if enterprise else "",
            product.product_code if product else "",
            product.product_name_cn if product else "",
            q.certificate_name,
            q.certificate_no,
            q.issuing_authority,
            q.issue_date.isoformat() if q.issue_date else "",
            q.expiry_date.isoformat() if q.expiry_date else "",
            计算证书状态(q.expiry_date),
            剩余天数,
            "是" if q.affects_recommendation else "否",
        ])
    return 表头, rows


def 导出匹配表():
    表头 = ["需求编号", "外资客户", "企业编号", "企业名称", "产品编号", "产品名称", "匹配得分", "推荐状态", "匹配原因", "风险提示", "更新时间"]
    demand_map = {d.id: d for d in Demand.query.all()}
    client_map = {c.id: c for c in ForeignClient.query.all()}
    enterprise_map = {e.id: e for e in Enterprise.query.all()}
    product_map = {p.id: p for p in Product.query.all()}
    rows = []
    for m in MatchRecord.query.order_by(MatchRecord.updated_at.desc()).all():
        demand = demand_map.get(m.demand_id)
        enterprise = enterprise_map.get(m.enterprise_id)
        product = product_map.get(m.product_id)
        client = client_map.get(demand.foreign_client_id) if demand else None
        rows.append([
            demand.demand_code if demand else "",
            client.client_name if client else "",
            enterprise.enterprise_code if enterprise else "",
            enterprise.company_name if enterprise else "",
            product.product_code if product else "",
            product.product_name_cn if product else "",
            float(m.match_score) if m.match_score is not None else None,
            m.recommendation_status,
            m.match_reason,
            m.risk_notes,
            m.updated_at.strftime("%Y-%m-%d %H:%M:%S") if m.updated_at else "",
        ])
    return 表头, rows


def 导出项目表():
    表头 = ["项目编号", "企业编号", "企业名称", "产品编号", "产品名称", "外资客户", "需求编号", "当前阶段", "项目负责人", "样品状态", "报价状态", "合同状态", "成交金额", "下步动作", "更新时间"]
    demand_map = {d.id: d for d in Demand.query.all()}
    client_map = {c.id: c for c in ForeignClient.query.all()}
    enterprise_map = {e.id: e for e in Enterprise.query.all()}
    product_map = {p.id: p for p in Product.query.all()}
    rows = []
    for p in ProjectProgress.query.order_by(ProjectProgress.updated_at.desc()).all():
        enterprise = enterprise_map.get(p.enterprise_id)
        product = product_map.get(p.product_id)
        client = client_map.get(p.foreign_client_id)
        demand = demand_map.get(p.demand_id)
        rows.append([
            项目编号(p),
            enterprise.enterprise_code if enterprise else "",
            enterprise.company_name if enterprise else "",
            product.product_code if product else "",
            product.product_name_cn if product else "",
            client.client_name if client else "",
            demand.demand_code if demand else "",
            p.current_stage,
            p.project_owner,
            p.sample_status,
            p.quotation_status,
            p.contract_status,
            float(p.deal_amount) if p.deal_amount is not None else None,
            p.next_action,
            p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else "",
        ])
    return 表头, rows


def 填充项目字段(project, form):
    project.enterprise_id = form.get("enterprise_id", type=int)
    project.product_id = form.get("product_id", type=int)
    project.foreign_client_id = form.get("foreign_client_id", type=int)
    project.demand_id = form.get("demand_id", type=int)
    project.current_stage = form.get("current_stage", "").strip() or "待补充资料"
    project.first_contact_date = 读取日期(form.get("first_contact_date"))
    project.material_sent_date = 读取日期(form.get("material_sent_date"))
    project.sample_status = form.get("sample_status", "").strip() or None
    project.quotation_status = form.get("quotation_status", "").strip() or None
    project.negotiation_status = form.get("negotiation_status", "").strip() or None
    project.contract_status = form.get("contract_status", "").strip() or None
    project.deal_amount = 读取金额(form.get("deal_amount"))
    project.next_action = form.get("next_action", "").strip() or None
    project.project_owner = form.get("project_owner", "").strip() or None
    project.notes = form.get("notes", "").strip() or None


def 项目编号(project):
    if not project:
        return "-"
    return f"P{project.id:04d}" if project.id else "P-待生成"


def 构建项目时间线(project):
    timeline = []
    if project.first_contact_date:
        timeline.append({"date": project.first_contact_date, "title": "首次对接", "desc": "已与客户建立初步沟通。"})
    if project.material_sent_date:
        timeline.append({"date": project.material_sent_date, "title": "资料发送", "desc": "已发送企业/产品资料。"})
    if project.sample_status and project.sample_status != "未涉及":
        timeline.append({"date": None, "title": "样品状态", "desc": project.sample_status})
    if project.quotation_status:
        timeline.append({"date": None, "title": "报价状态", "desc": project.quotation_status})
    if project.negotiation_status:
        timeline.append({"date": None, "title": "谈判状态", "desc": project.negotiation_status})
    if project.contract_status:
        timeline.append({"date": None, "title": "合同状态", "desc": project.contract_status})
    timeline.append({"date": project.updated_at.date() if project.updated_at else None, "title": "最近更新", "desc": project.current_stage or "阶段未设置"})
    return timeline


def 统一关键词集合(text):
    if not text:
        return set()
    return {item.lower() for item in re.split(r"[\s,，;；/|]+", text) if item.strip()}


def 文本匹配关键词(tokens, text):
    值 = (text or "").lower()
    return any(token in 值 for token in tokens)


def 读取生产周期天数(text):
    if not text:
        return None
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else None


def 计算匹配得分(demand, product, enterprise):
    score = 0
    reasons = []
    risks = []

    关键词 = 统一关键词集合(demand.product_keywords)
    if 关键词 and (
        文本匹配关键词(关键词, product.product_name_cn)
        or 文本匹配关键词(关键词, product.product_category)
        or 文本匹配关键词(关键词, enterprise.main_products)
    ):
        score += 30
        reasons.append("关键词与产品名称/类别/主营产品匹配")
    else:
        risks.append("关键词匹配度较弱")

    市场关键词 = 统一关键词集合(demand.target_market)
    if not 市场关键词:
        reasons.append("需求未限定目标市场")
    elif (
        文本匹配关键词(市场关键词, product.target_market)
        or 文本匹配关键词(市场关键词, product.existing_sales_countries)
        or 文本匹配关键词(市场关键词, enterprise.target_markets)
        or 文本匹配关键词(市场关键词, enterprise.export_countries)
    ):
        score += 20
        reasons.append("目标市场或出口国家匹配")
    else:
        risks.append("目标市场匹配不足")

    认证关键词 = 统一关键词集合(demand.required_certifications)
    if not 认证关键词:
        reasons.append("需求未要求特定认证")
    elif all(token in (product.certifications or "").lower() for token in 认证关键词):
        score += 20
        reasons.append("认证要求满足")
    else:
        risks.append("认证要求可能不完整")

    交期天数 = 读取生产周期天数(demand.delivery_requirement)
    生产天数 = 读取生产周期天数(product.production_cycle)
    if 交期天数 is None or 生产天数 is None:
        risks.append("缺少明确交期/生产周期数据")
    elif 生产天数 <= 交期天数:
        score += 10
        reasons.append("生产周期满足交期要求")
    else:
        risks.append("生产周期可能偏长")

    价格候选 = [price for price in [product.exw_price, product.fob_price, product.cif_price, product.ddp_price] if price is not None]
    if not demand.target_price:
        reasons.append("需求未提供目标价格")
    elif 价格候选 and min(价格候选) <= demand.target_price:
        score += 10
        reasons.append("报价存在且不高于目标价格")
    else:
        risks.append("价格可能高于目标价或缺少报价")

    if enterprise.has_foreign_trade_experience:
        score += 10
        reasons.append("企业具备外贸经验")
    else:
        risks.append("企业外贸经验有限")

    return min(score, 100), reasons, risks


def 计算推荐状态(score):
    if score >= 80:
        return "高度匹配"
    if score >= 60:
        return "可进一步沟通"
    return "谨慎推荐"


def 读取布尔(form, 字段名):
    return form.get(字段名) == "on"


def 读取日期(值):
    if not 值:
        return None
    try:
        return datetime.strptime(值, "%Y-%m-%d").date()
    except ValueError:
        return None


def 读取整数(值):
    if not 值:
        return None
    try:
        return int(值)
    except ValueError:
        return None


def 读取金额(值):
    if not 值:
        return None
    try:
        return Decimal(值)
    except (InvalidOperation, ValueError):
        return None


def 读取布尔文本(值):
    return str(值 or "").strip().lower() in {"1", "true", "yes", "y", "是", "已", "on"}


def csv_safe(value):
    text = "" if value is None else str(value)
    text = text.replace('"', '""')
    return f'"{text}"'


def 单元格文本(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    return str(value).strip()


def 导入企业Excel(file_storage):
    rows = list(csv.reader(file_storage.stream.read().decode("utf-8-sig").splitlines()))
    if not rows:
        return 0, [{"行号": 1, "原因": "文件为空", "数据": {}}]
    header = [单元格文本(c) for c in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    必填 = ["企业名称"]
    缺失 = [f for f in 必填 if f not in idx]
    if 缺失:
        return 0, [{"行号": 1, "原因": f"缺少必填列: {', '.join(缺失)}", "数据": {}}]

    success = 0
    failed = []
    for row_num, row in enumerate(rows[1:], start=2):
        try:
            company_name = 单元格文本(row[idx["企业名称"]])
            if not company_name:
                raise ValueError("企业名称不能为空")
            enterprise_code = 单元格文本(row[idx["企业编号"]]) if "企业编号" in idx else ""
            enterprise = Enterprise.query.filter_by(enterprise_code=enterprise_code).first() if enterprise_code else None
            if not enterprise:
                enterprise = Enterprise(enterprise_code=enterprise_code or 生成企业编号())
                db.session.add(enterprise)

            enterprise.company_name = company_name
            enterprise.english_name = 单元格文本(row[idx["英文名称"]]) or None if "英文名称" in idx else None
            enterprise.unified_social_credit_code = 单元格文本(row[idx["统一社会信用代码"]]) or None if "统一社会信用代码" in idx else None
            enterprise.industry_category = 单元格文本(row[idx["行业类别"]]) or None if "行业类别" in idx else None
            enterprise.main_products = 单元格文本(row[idx["主营产品"]]) or None if "主营产品" in idx else None
            enterprise.export_countries = 单元格文本(row[idx["已出口国家"]]) or None if "已出口国家" in idx else None
            enterprise.target_markets = 单元格文本(row[idx["目标市场"]]) or None if "目标市场" in idx else None
            enterprise.status = 单元格文本(row[idx["状态"]]) or "草稿" if "状态" in idx else "草稿"
            enterprise.project_owner = 单元格文本(row[idx["项目负责人"]]) or None if "项目负责人" in idx else None
            success += 1
        except Exception as exc:
            failed.append({"行号": row_num, "原因": str(exc), "数据": {"企业编号": row[idx["企业编号"]] if "企业编号" in idx else "", "企业名称": row[idx["企业名称"]] if "企业名称" in idx else ""}})
    db.session.commit()
    return success, failed


def 导入产品Excel(file_storage):
    rows = list(csv.reader(file_storage.stream.read().decode("utf-8-sig").splitlines()))
    if not rows:
        return 0, [{"行号": 1, "原因": "文件为空", "数据": {}}]
    header = [单元格文本(c) for c in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    必填 = ["企业编号", "产品中文名"]
    缺失 = [f for f in 必填 if f not in idx]
    if 缺失:
        return 0, [{"行号": 1, "原因": f"缺少必填列: {', '.join(缺失)}", "数据": {}}]

    enterprise_map = {e.enterprise_code: e for e in Enterprise.query.all()}
    success = 0
    failed = []
    for row_num, row in enumerate(rows[1:], start=2):
        try:
            enterprise_code = 单元格文本(row[idx["企业编号"]])
            if not enterprise_code:
                raise ValueError("企业编号不能为空")
            enterprise = enterprise_map.get(enterprise_code)
            if not enterprise:
                raise ValueError(f"未找到企业编号 {enterprise_code}")
            name_cn = 单元格文本(row[idx["产品中文名"]])
            if not name_cn:
                raise ValueError("产品中文名不能为空")
            product_code = 单元格文本(row[idx["产品编号"]]) if "产品编号" in idx else ""
            product = Product.query.filter_by(product_code=product_code, enterprise_id=enterprise.id).first() if product_code else None
            if not product:
                product = Product(
                    enterprise_id=enterprise.id,
                    product_code=product_code or generate_product_code(enterprise.id),
                )
                db.session.add(product)

            product.enterprise_id = enterprise.id
            product.product_name_cn = name_cn
            product.product_name_en = 单元格文本(row[idx["产品英文名"]]) or None if "产品英文名" in idx else None
            product.product_category = 单元格文本(row[idx["产品类别"]]) or None if "产品类别" in idx else None
            product.hs_code = 单元格文本(row[idx["HS编码"]]) or None if "HS编码" in idx else None
            product.model = 单元格文本(row[idx["型号"]]) or None if "型号" in idx else None
            if "FOB价格" in idx:
                product.fob_price = 读取金额(单元格文本(row[idx["FOB价格"]]))
            product.currency = 单元格文本(row[idx["币种"]]) or "USD" if "币种" in idx else "USD"
            product.target_market = 单元格文本(row[idx["目标市场"]]) or None if "目标市场" in idx else None
            product.certifications = 单元格文本(row[idx["认证"]]) or None if "认证" in idx else None
            if "支持定制" in idx:
                product.customization_supported = 读取布尔文本(row[idx["支持定制"]])
            success += 1
        except Exception as exc:
            failed.append({"行号": row_num, "原因": str(exc), "数据": {"企业编号": row[idx["企业编号"]] if "企业编号" in idx else "", "产品中文名": row[idx["产品中文名"]] if "产品中文名" in idx else ""}})
    db.session.commit()
    return success, failed


def 获取证书类型选项():
    return [
        "基础证照",
        "生产资质",
        "外贸资质",
        "质量体系认证",
        "产品认证",
        "知识产权",
        "合规文件",
        "其他",
    ]


def 计算证书状态(到期日期):
    if not 到期日期:
        return "未填写"
    剩余天数 = (到期日期 - date.today()).days
    if 剩余天数 < 0:
        return "已过期"
    if 剩余天数 <= 90:
        return "即将到期"
    return "正常"


def 构建证照展示项(资质):
    证书状态 = 计算证书状态(资质.expiry_date)
    剩余天数 = (资质.expiry_date - date.today()).days if 资质.expiry_date else None
    状态样式 = {
        "已过期": "danger",
        "即将到期": "warning",
        "正常": "success",
        "未填写": "secondary",
    }
    return {
        "记录": 资质,
        "证书状态": 证书状态,
        "剩余天数": 剩余天数,
        "状态样式": 状态样式.get(证书状态, "secondary"),
    }


def 包含非法文件名字符(名称):
    return bool(re.search(r'[\\/:*?"<>|]', 名称 or ""))


def 清洗路径片段(名称):
    return re.sub(r'[\\/:*?"<>|]+', "_", (名称 or "").strip())


def 获取文件分类目录(document_type):
    return DOCUMENT_FOLDER_MAPPING.get((document_type or "").upper(), DOCUMENT_FOLDER_MAPPING["OTHER"])


def 构建标准文件名(enterprise_code, product_code, document_type, document_name, version, date_text, uploaded_by, extension):
    安全文件名 = 清洗路径片段(document_name)
    安全上传人 = 清洗路径片段(uploaded_by)
    片段 = [enterprise_code]
    if product_code:
        片段.append(product_code)
    片段.extend([document_type, 安全文件名, version, date_text, 安全上传人])
    return "_".join(片段) + extension


def 生成不覆盖文件路径(目标路径):
    if not 目标路径.exists():
        return 目标路径
    时间戳 = datetime.now().strftime("%H%M%S")
    return 目标路径.with_name(f"{目标路径.stem}_{时间戳}{目标路径.suffix}")


def 包含关键词(文本, 关键词列表):
    内容 = (文本 or "").upper()
    return any(关键词 in 内容 for 关键词 in 关键词列表)


def 生成出海方案分析(企业, 产品列表, 资质列表, 文件列表):
    认证关键词 = ["CE", "FDA", "UL", "REACH", "ROHS", "ETL", "FCC", "ISO"]
    宣传类型 = {"PPT", "IMG", "VIDEO"}
    产品资料类型 = {"PROD", "SPEC"}
    合规资料类型 = {"CERT", "AUTH", "CONTRACT"}

    有外贸经验 = bool(企业.has_foreign_trade_experience or 企业.export_revenue or 企业.export_countries)
    有目标市场认证 = any(
        包含关键词(资质.certificate_name, 认证关键词) or 包含关键词(资质.certificate_type, 认证关键词)
        for 资质 in 资质列表
    ) or any(包含关键词(产品.certifications, 认证关键词) for 产品 in 产品列表)
    有完整产品资料 = any(
        (产品.product_name_en or "").strip() and ((产品.specification or "").strip() or (产品.function_description or "").strip())
        for 产品 in 产品列表
    ) and any((文件.document_type or "").upper() in 产品资料类型 for 文件 in 文件列表)
    有清晰报价和MOQ = any(
        (产品.moq or "").strip()
        and any([产品.exw_price is not None, 产品.fob_price is not None, 产品.cif_price is not None, 产品.ddp_price is not None])
        for 产品 in 产品列表
    )
    有稳定产能和生产周期 = bool(企业.annual_capacity) and any(
        (产品.monthly_capacity or "").strip() and (产品.production_cycle or "").strip() for 产品 in 产品列表
    )
    有目标市场或已出口国家 = bool(企业.target_markets or 企业.export_countries) or any(
        (产品.target_market or "").strip() or (产品.existing_sales_countries or "").strip() for 产品 in 产品列表
    )
    有合规文件和证照 = bool(资质列表) or any((文件.document_type or "").upper() in 合规资料类型 for 文件 in 文件列表)
    有宣传资料 = any((文件.document_type or "").upper() in 宣传类型 for 文件 in 文件列表)

    评分项 = [
        {"名称": "是否有外贸经验", "分值": 15, "达成": 有外贸经验},
        {"名称": "是否有目标市场认证", "分值": 20, "达成": 有目标市场认证},
        {"名称": "是否有完整产品资料", "分值": 15, "达成": 有完整产品资料},
        {"名称": "是否有清晰报价和 MOQ", "分值": 10, "达成": 有清晰报价和MOQ},
        {"名称": "是否有稳定产能和生产周期", "分值": 15, "达成": 有稳定产能和生产周期},
        {"名称": "是否有目标市场或已出口国家", "分值": 10, "达成": 有目标市场或已出口国家},
        {"名称": "是否有合规文件和证照", "分值": 10, "达成": 有合规文件和证照},
        {"名称": "是否有宣传资料/PPT/影像资料", "分值": 5, "达成": 有宣传资料},
    ]
    成熟度分数 = sum(项["分值"] for 项 in 评分项 if 项["达成"])

    标签 = []
    if 成熟度分数 >= 80 and 有目标市场认证 and 有清晰报价和MOQ:
        标签.extend(["外贸成熟型", "适合重点推荐"])
    elif 成熟度分数 >= 55:
        标签.append("产品潜力型")
    if not 有完整产品资料:
        标签.append("资料待完善型")
    if not 有目标市场认证:
        标签.append("认证缺失型")
    if not 有清晰报价和MOQ:
        标签.append("价格待确认型")
    if not 有稳定产能和生产周期:
        标签.append("产能风险型")
    if "适合重点推荐" not in 标签:
        标签.append("适合先辅导再推荐")

    优势说明 = []
    风险提示 = []
    下一步建议 = []

    if 有外贸经验 and 有目标市场或已出口国家:
        优势说明.append("具备一定外贸经验与目标市场信息，可快速进入客户匹配环节。")
        下一步建议.append("优先推荐给已有明确采购需求的外资客户")
    if 有完整产品资料:
        优势说明.append("产品基础资料较完整，可支持初步评估和商机沟通。")
    else:
        风险提示.append("产品英文资料/规格书不完整，影响外资客户快速评估。")
        下一步建议.append("先补充产品英文资料、规格书和报价单")
    if 有目标市场认证:
        优势说明.append("已具备目标市场相关认证基础，有助于缩短准入周期。")
    else:
        风险提示.append("缺少关键目标市场认证，存在准入障碍。")
        下一步建议.append("先完善目标市场认证，例如 CE/FDA/UL/REACH 等")
    if not 有稳定产能和生产周期:
        风险提示.append("产能或生产周期信息不足，交付稳定性待确认。")
        下一步建议.append("需要进一步核实产能、交期和供货稳定性")
    if 成熟度分数 >= 60:
        下一步建议.append("适合参加海外展会或线上 B2B 平台测试")
        下一步建议.append("适合做目标市场准入与竞品价格分析")
    if 有清晰报价和MOQ:
        下一步建议.append("适合先进行样品测试和小批量订单撮合")
    else:
        风险提示.append("报价或 MOQ 信息不明确，影响商务推进效率。")
    if not 有合规文件和证照:
        风险提示.append("基础合规文件不充分，当前推荐风险较高。")
        下一步建议.append("暂不建议对外推荐，需补齐基础资质或合规文件")

    if not 优势说明:
        优势说明.append("企业具备一定生产与产品基础，可通过辅导逐步进入推荐池。")
    if not 风险提示:
        风险提示.append("当前未发现显著短板，建议继续维护资料与交付稳定性。")

    下一步建议 = list(dict.fromkeys(下一步建议))
    标签 = list(dict.fromkeys(标签))

    return {
        "成熟度分数": 成熟度分数,
        "评分项": 评分项,
        "标签": 标签,
        "优势说明": 优势说明,
        "风险提示": 风险提示,
        "下一步建议": 下一步建议,
    }


def init_db(app):
    """初始化数据库与基础账号。"""

    with app.app_context():
        db.create_all()
        管理员 = User.query.filter_by(username="admin").first()
        if not 管理员:
            db.session.add(User(username="admin", password=generate_password_hash("admin123"), role="管理员"))
        elif not 管理员.password.startswith("pbkdf2:") and not 管理员.password.startswith("scrypt:"):
            管理员.password = generate_password_hash("admin123")
            管理员.role = "管理员"
        if not User.query.filter_by(username="user").first():
            db.session.add(User(username="user", password=generate_password_hash("user123"), role="普通用户"))
        db.session.commit()

        backup_root = app.config["BACKUP_ROOT"]
        backup_root.mkdir(parents=True, exist_ok=True)
        today_prefix = f"backup_db_{datetime.now().strftime('%Y%m%d')}"
        has_today_backup = any(path.name.startswith(today_prefix) for path in backup_root.glob("backup_db_*.sqlite"))
        if not has_today_backup:
            src = BASE_DIR / "trade_agent.db"
            dst = backup_root / f"backup_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite"
            shutil.copy2(src, dst)


app = create_app()

if __name__ == "__main__":
    init_db(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
