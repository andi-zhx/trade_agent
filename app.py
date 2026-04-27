from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from flask import Flask, flash, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from models import Demand, Document, Enterprise, MatchRecord, Product, Qualification, User, db

BASE_DIR = Path(__file__).resolve().parent


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


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "replace-with-a-secure-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'trade_agent.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.template_filter("currency")
    def currency_filter(value, currency="USD"):
        if value is None:
            return "-"
        return f"{currency} {value:,.2f}"

    @app.route("/")
    def dashboard():
        企业数量 = Enterprise.query.count()
        产品数量 = Product.query.count()
        需求数量 = Demand.query.count()
        撮合数量 = MatchRecord.query.count()

        核心模块 = [
            {"名称": "企业库管理", "说明": "维护国内企业基础信息、联系人及出海目标。", "链接": url_for("enterprise_list")},
            {"名称": "产品管理", "说明": "管理企业产品信息、品类与产品描述。", "链接": url_for("product_list")},
            {"名称": "资质证照", "说明": "维护企业相关资质证照、编号和有效期。", "链接": "#"},
            {"名称": "外资客户需求", "说明": "记录海外客户需求与目标采购方向。", "链接": "#"},
            {"名称": "撮合进展", "说明": "跟踪撮合过程、阶段状态与跟进记录。", "链接": "#"},
            {"名称": "归档文件", "说明": "统一存放项目过程文档与归档资料。", "链接": "#"},
        ]

        return render_template(
            "dashboard.html",
            企业数量=企业数量,
            产品数量=产品数量,
            需求数量=需求数量,
            撮合数量=撮合数量,
            核心模块=核心模块,
        )

    @app.route("/登录", methods=["GET", "POST"])
    def 登录():
        if request.method == "POST":
            用户名 = request.form.get("用户名", "").strip()
            密码 = request.form.get("密码", "").strip()

            用户 = User.query.filter_by(username=用户名, password=密码).first()
            if 用户:
                session["用户"] = 用户.username
                flash("登录成功", "success")
                return redirect(url_for("dashboard"))

            flash("用户名或密码错误", "danger")

        return render_template("login.html")

    @app.route("/退出")
    def 退出():
        session.pop("用户", None)
        flash("已退出登录", "info")
        return redirect(url_for("登录"))

    @app.route("/enterprises")
    def enterprise_list():
        enterprises = Enterprise.query.order_by(Enterprise.enterprise_code.asc()).all()
        return render_template("enterprise_list.html", enterprises=enterprises)

    @app.route("/enterprises/<int:enterprise_id>")
    def enterprise_detail(enterprise_id):
        enterprise = Enterprise.query.get_or_404(enterprise_id)
        products = Product.query.filter_by(enterprise_id=enterprise.id).order_by(Product.created_at.desc()).all()
        return render_template("enterprise_detail.html", enterprise=enterprise, products=products)

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
            fill_product_from_form(product, request.form)
            db.session.add(product)
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
        archive_code = f"{enterprise.enterprise_code}_{product.product_code}" if enterprise else product.product_code
        return render_template(
            "products/detail.html",
            product=product,
            enterprise=enterprise,
            certificates=certificates,
            product_files=product_files,
            archive_code=archive_code,
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
            fill_product_from_form(product, request.form)
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
    def product_delete(product_id):
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        flash("产品已删除。", "info")
        return redirect(url_for("product_list"))

    @app.cli.command("init-db")
    def init_db_command():
        """初始化数据库（可选：flask init-db）。"""

        init_db(app)

    return app


def parse_decimal(value):
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


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
    product.customization_supported = form.get("customization_supported") == "on"
    product.exw_price = parse_decimal(form.get("exw_price", "").strip())
    product.fob_price = parse_decimal(form.get("fob_price", "").strip())
    product.cif_price = parse_decimal(form.get("cif_price", "").strip())
    product.ddp_price = parse_decimal(form.get("ddp_price", "").strip())
    product.currency = form.get("currency", "USD").strip() or "USD"
    product.quote_date = parse_date(form.get("quote_date", "").strip())
    product.quote_valid_until = parse_date(form.get("quote_valid_until", "").strip())
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


def generate_product_code(enterprise_id):
    products = Product.query.filter_by(enterprise_id=enterprise_id).all()
    max_no = 0
    for p in products:
        if p.product_code:
            match = re.fullmatch(r"P(\d{3})", p.product_code)
            if match:
                max_no = max(max_no, int(match.group(1)))
    return f"P{max_no + 1:03d}"


def init_db(app):
    """初始化数据库与基础账号。"""

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="admin123"))
            db.session.commit()


app = create_app()

if __name__ == "__main__":
    init_db(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
