from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from flask import Flask, flash, redirect, render_template, request, send_from_directory, session, url_for
from sqlalchemy import func, or_

from models import (
    Contact,
    Demand,
    Document,
    Enterprise,
    ForeignClient,
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
        项目总数 = ProjectProgress.query.count()
        已成交项目数 = ProjectProgress.query.filter(ProjectProgress.current_stage == "已成交").count()
        商务谈判中项目数 = ProjectProgress.query.filter(ProjectProgress.current_stage == "商务谈判中").count()
        本月起始日期 = date.today().replace(day=1)
        本月新增项目数 = ProjectProgress.query.filter(ProjectProgress.created_at >= datetime.combine(本月起始日期, datetime.min.time())).count()
        总成交金额 = db.session.query(func.coalesce(func.sum(ProjectProgress.deal_amount), 0)).scalar() or Decimal("0")
        资质总数 = Qualification.query.count()
        已过期证书数量 = sum(1 for 资质 in Qualification.query.all() if 计算证书状态(资质.expiry_date) == "已过期")
        九十天内到期证书数量 = sum(1 for 资质 in Qualification.query.all() if 计算证书状态(资质.expiry_date) == "即将到期")

        核心模块 = [
            {"名称": "企业库管理", "说明": "维护国内企业基础信息、联系人及出海目标。", "链接": url_for("enterprise_list")},
            {"名称": "产品管理", "说明": "管理企业产品信息、品类与产品描述。", "链接": "#"},
            {"名称": "资质证照", "说明": "维护企业相关资质证照、编号和有效期。", "链接": url_for("qualification_list")},
            {"名称": "外资客户需求", "说明": "记录海外客户需求与目标采购方向。", "链接": url_for("demand_list")},
            {"名称": "撮合进展", "说明": "跟踪撮合过程、阶段状态与跟进记录。", "链接": url_for("project_list")},
            {"名称": "归档文件", "说明": "统一存放项目过程文档与归档资料。", "链接": url_for("document_list")},
        ]

        return render_template(
            "dashboard.html",
            企业数量=企业数量,
            产品数量=产品数量,
            需求数量=需求数量,
            撮合数量=撮合数量,
            项目总数=项目总数,
            已成交项目数=已成交项目数,
            商务谈判中项目数=商务谈判中项目数,
            本月新增项目数=本月新增项目数,
            总成交金额=总成交金额,
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
        匹配记录 = (
            MatchRecord.query.filter_by(enterprise_id=id)
            .order_by(MatchRecord.match_score.desc(), MatchRecord.updated_at.desc())
            .all()
        )
        匹配需求列表 = [
            {
                "记录": 记录,
                "需求": Demand.query.get(记录.demand_id),
                "产品": Product.query.get(记录.product_id) if 记录.product_id else None,
                "客户": ForeignClient.query.get(Demand.query.get(记录.demand_id).foreign_client_id) if Demand.query.get(记录.demand_id) else None,
            }
            for 记录 in 匹配记录
        ]

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
            匹配需求列表=匹配需求列表,
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
