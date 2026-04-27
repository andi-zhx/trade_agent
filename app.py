from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from flask import Flask, flash, redirect, render_template, request, send_from_directory, session, url_for
from sqlalchemy import or_

from models import (
    Contact,
    Demand,
    Document,
    Enterprise,
    MatchRecord,
    Product,
    ProjectProgress,
    Qualification,
    User,
    db,
)

BASE_DIR = Path(__file__).resolve().parent
PER_PAGE = 10


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


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "replace-with-a-secure-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'trade_agent.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_ROOT"] = BASE_DIR / "uploads" / "企业库"

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
        资质总数 = Qualification.query.count()
        已过期证书数量 = sum(1 for 资质 in Qualification.query.all() if 计算证书状态(资质.expiry_date) == "已过期")
        九十天内到期证书数量 = sum(1 for 资质 in Qualification.query.all() if 计算证书状态(资质.expiry_date) == "即将到期")

        核心模块 = [
            {"名称": "企业库管理", "说明": "维护国内企业基础信息、联系人及出海目标。", "链接": url_for("enterprise_list")},
            {"名称": "产品管理", "说明": "管理企业产品信息、品类与产品描述。", "链接": "#"},
            {"名称": "资质证照", "说明": "维护企业相关资质证照、编号和有效期。", "链接": url_for("qualification_list")},
            {"名称": "外资客户需求", "说明": "记录海外客户需求与目标采购方向。", "链接": "#"},
            {"名称": "撮合进展", "说明": "跟踪撮合过程、阶段状态与跟进记录。", "链接": "#"},
            {"名称": "归档文件", "说明": "统一存放项目过程文档与归档资料。", "链接": url_for("document_list")},
        ]

        return render_template(
            "dashboard.html",
            企业数量=企业数量,
            产品数量=产品数量,
            需求数量=需求数量,
            撮合数量=撮合数量,
            资质总数=资质总数,
            已过期证书数量=已过期证书数量,
            九十天内到期证书数量=九十天内到期证书数量,
            核心模块=核心模块,
        )

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
        进展列表 = ProjectProgress.query.filter_by(enterprise_id=id).order_by(ProjectProgress.updated_at.desc()).all()

        建议 = 生成出海建议(企业)

        return render_template(
            "enterprise_detail.html",
            企业=企业,
            联系人列表=联系人列表,
            产品列表=产品列表,
            资质列表=资质列表,
            资质展示列表=资质展示列表,
            文件列表=文件列表,
            进展列表=进展列表,
            建议=建议,
        )

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
    def enterprise_delete(id):
        企业 = Enterprise.query.get_or_404(id)
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

            企业目录 = app.config["UPLOAD_ROOT"] / f"{enterprise.enterprise_code}_{清洗路径片段(enterprise.company_name)}"
            if product:
                归档目录 = 企业目录 / "05_产品资料" / f"{enterprise.enterprise_code}_{product.product_code}_{清洗路径片段(product.product_name_cn)}"
            else:
                归档目录 = 企业目录 / 获取文件分类目录(document_type)
            归档目录.mkdir(parents=True, exist_ok=True)

            扩展名 = Path(上传文件.filename).suffix.lower()
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
                original_filename=上传文件.filename,
                uploaded_by=uploaded_by,
                notes=notes,
            )
            db.session.add(document)
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


def 生成出海建议(企业):
    建议 = []
    if not 企业.has_foreign_trade_experience:
        建议.append("建议优先开展外贸合规培训，并配置英文产品资料包。")
    if not 企业.export_countries:
        建议.append("建议先从东南亚与中东等准入门槛较低市场切入。")
    if 企业.is_manufacturer and 企业.main_equipment:
        建议.append("可突出制造能力，优先匹配 OEM/ODM 类采购需求。")
    if 企业.risk_notes:
        建议.append("已记录风险备注，建议在项目立项前完成风控复核。")
    if not 建议:
        建议.append("企业基础条件较完善，可进入重点客户定向推荐池。")
    return 建议


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
