from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

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


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "replace-with-a-secure-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'trade_agent.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/")
    def dashboard():
        企业数量 = Enterprise.query.count()
        产品数量 = Product.query.count()
        需求数量 = Demand.query.count()
        撮合数量 = MatchRecord.query.count()

        核心模块 = [
            {"名称": "企业库管理", "说明": "维护国内企业基础信息、联系人及出海目标。", "链接": url_for("enterprise_list")},
            {"名称": "产品管理", "说明": "管理企业产品信息、品类与产品描述。", "链接": "#"},
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
        资质列表 = Qualification.query.filter_by(enterprise_id=id).all()
        文件列表 = Document.query.filter_by(enterprise_id=id).all()
        进展列表 = ProjectProgress.query.filter_by(enterprise_id=id).order_by(ProjectProgress.updated_at.desc()).all()

        建议 = 生成出海建议(企业)

        return render_template(
            "enterprise_detail.html",
            企业=企业,
            联系人列表=联系人列表,
            产品列表=产品列表,
            资质列表=资质列表,
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
