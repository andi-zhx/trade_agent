from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(db.Model):
    """系统用户（当前用于登录演示）。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), default="管理员")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class Enterprise(db.Model):
    """企业信息表。"""

    __tablename__ = "enterprises"

    id = db.Column(db.Integer, primary_key=True)
    enterprise_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    company_name = db.Column(db.String(255), nullable=False, index=True)
    english_name = db.Column(db.String(255))
    unified_social_credit_code = db.Column(db.String(64), index=True)
    founded_date = db.Column(db.Date)
    registered_capital = db.Column(db.String(100))
    registered_address = db.Column(db.String(255))
    business_address = db.Column(db.String(255))
    province = db.Column(db.String(50), index=True)
    city = db.Column(db.String(50), index=True)
    district = db.Column(db.String(50))
    company_type = db.Column(db.String(100))
    industry_code = db.Column(db.String(50), index=True)
    industry_category = db.Column(db.String(100), index=True)
    sub_industry = db.Column(db.String(100))
    main_products = db.Column(db.Text)
    main_business = db.Column(db.Text)
    is_manufacturer = db.Column(db.Boolean, default=False, nullable=False)
    is_trader = db.Column(db.Boolean, default=False, nullable=False)
    is_brand_owner = db.Column(db.Boolean, default=False, nullable=False)
    is_oem_odm = db.Column(db.Boolean, default=False, nullable=False)
    is_service_provider = db.Column(db.Boolean, default=False, nullable=False)
    is_high_tech = db.Column(db.Boolean, default=False, nullable=False)
    is_specialized_new = db.Column(db.Boolean, default=False, nullable=False)
    is_listed_or_pre_ipo = db.Column(db.Boolean, default=False, nullable=False)
    has_foreign_trade_experience = db.Column(db.Boolean, default=False, nullable=False)
    export_countries = db.Column(db.Text)
    target_markets = db.Column(db.Text)
    annual_capacity = db.Column(db.String(255))
    employee_count = db.Column(db.Integer)
    factory_area = db.Column(db.String(100))
    main_equipment = db.Column(db.Text)
    annual_revenue = db.Column(db.Numeric(18, 2))
    export_revenue = db.Column(db.Numeric(18, 2))
    service_needs = db.Column(db.Text)
    risk_notes = db.Column(db.Text)
    enterprise_extra_fields = db.Column(db.JSON)
    status = db.Column(db.String(50), default="draft", nullable=False, index=True)
    project_owner = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    products = db.relationship('Product', back_populates='enterprise', lazy='dynamic')
    analysis_note = db.relationship(
        "EnterpriseAnalysisNote",
        back_populates="enterprise",
        uselist=False,
        cascade="all, delete-orphan",
    )


class EnterpriseAnalysisNote(db.Model):
    """企业出海分析备注。"""

    __tablename__ = "enterprise_analysis_notes"

    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    enterprise = db.relationship("Enterprise", back_populates="analysis_note")


class Contact(db.Model):
    """企业联系人表。"""

    __tablename__ = "contacts"

    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False
    )
    contact_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    wechat = db.Column(db.String(100))
    notes = db.Column(db.Text)


class Product(db.Model):
    """产品信息表。"""

    __tablename__ = "products"

    PRODUCT_TYPE_OPTIONS = ["标准品", "定制品", "OEM", "ODM", "工程项目型", "服务型", "数字产品", "其他"]
    EXPORT_SUITABILITY_OPTIONS = ["适合", "基本适合", "待补充资料", "暂不适合", "待判断"]
    RECOMMENDATION_LEVEL_OPTIONS = ["A优先推荐", "B可推荐", "C待完善", "D暂缓", "待评估"]
    PRODUCT_STATUS_OPTIONS = ["草稿", "待补充", "已入库", "已推荐", "暂停", "下架"]
    CERTIFICATION_STATUS_OPTIONS = ["齐全", "部分齐全", "待补充", "无需认证", "未核验"]

    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False
    )
    product_code = db.Column(db.String(32), nullable=False, index=True)
    main_image = db.Column(db.String(500))
    product_name_cn = db.Column(db.String(255), nullable=False, index=True)
    product_name_en = db.Column(db.String(255))
    industry_code = db.Column(db.String(50), index=True)
    industry_name = db.Column(db.String(100), index=True)
    product_category = db.Column(db.String(100), index=True)
    product_type = db.Column(db.String(50), index=True)
    hs_code = db.Column(db.String(32), index=True)
    model = db.Column(db.String(100))
    brand = db.Column(db.String(100))
    material = db.Column(db.String(255))
    specification = db.Column(db.Text)
    size = db.Column(db.String(100))
    weight = db.Column(db.String(100))
    color = db.Column(db.String(100))
    function_description = db.Column(db.Text)
    application_scenario = db.Column(db.Text)
    unit = db.Column(db.String(20))
    moq = db.Column(db.String(50))
    production_cycle = db.Column(db.String(100))
    delivery_cycle = db.Column(db.String(100))
    sample_cycle = db.Column(db.String(100))
    monthly_capacity = db.Column(db.String(255))
    customization_supported = db.Column(db.Boolean, default=False, nullable=False)
    exw_price = db.Column(db.Numeric(18, 2))
    fob_price = db.Column(db.Numeric(18, 2))
    cif_price = db.Column(db.Numeric(18, 2))
    ddp_price = db.Column(db.Numeric(18, 2))
    price_display = db.Column(db.String(255))
    currency = db.Column(db.String(10), default="USD")
    quote_date = db.Column(db.Date)
    quote_valid_until = db.Column(db.Date)
    sample_policy = db.Column(db.Text)
    target_market = db.Column(db.String(255))
    export_suitability = db.Column(db.String(50), index=True)
    recommendation_level = db.Column(db.String(50), index=True)
    existing_sales_countries = db.Column(db.Text)
    certifications = db.Column(db.Text)
    certification_status = db.Column(db.String(50), index=True)
    packaging = db.Column(db.Text)
    carton_size = db.Column(db.String(100))
    gross_weight = db.Column(db.String(100))
    net_weight = db.Column(db.String(100))
    loading_quantity = db.Column(db.String(100))
    warranty = db.Column(db.String(255))
    product_selling_points = db.Column(db.Text)
    notes = db.Column(db.Text)
    product_extra_fields = db.Column(db.JSON)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    enterprise = db.relationship('Enterprise', back_populates='products')


class Qualification(db.Model):
    """资质证照表。"""

    __tablename__ = "qualifications"

    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"))
    certificate_name = db.Column(db.String(255), nullable=False)
    certificate_type = db.Column(db.String(100))
    certificate_no = db.Column(db.String(100), index=True)
    issuing_authority = db.Column(db.String(255))
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    covered_products = db.Column(db.Text)
    status = db.Column(db.String(50), index=True)
    affects_recommendation = db.Column(db.Boolean, default=False, nullable=False)
    file_path = db.Column(db.String(500))
    notes = db.Column(db.Text)

    enterprise = db.relationship("Enterprise", backref=db.backref("qualifications", lazy="dynamic"))
    product = db.relationship("Product", backref=db.backref("qualifications", lazy="dynamic"))


class ForeignClient(db.Model):
    """外资客户表。"""

    __tablename__ = "foreign_clients"

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(255), nullable=False, index=True)
    country_region = db.Column(db.String(100), index=True)
    company_type = db.Column(db.String(100))
    contact_name = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))
    contact_email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Demand(db.Model):
    """外资需求表。"""

    __tablename__ = "demands"

    id = db.Column(db.Integer, primary_key=True)
    foreign_client_id = db.Column(
        db.Integer, db.ForeignKey("foreign_clients.id", ondelete="CASCADE"), nullable=False
    )
    demand_code = db.Column(db.String(32), nullable=False, unique=True, index=True)
    purchase_category = db.Column(db.String(100), index=True)
    product_keywords = db.Column(db.Text)
    target_price = db.Column(db.Numeric(18, 2))
    purchase_quantity = db.Column(db.String(100))
    required_certifications = db.Column(db.Text)
    delivery_requirement = db.Column(db.String(255))
    trade_terms = db.Column(db.String(100))
    payment_terms = db.Column(db.String(100))
    target_market = db.Column(db.String(255))
    priority = db.Column(db.String(50), default="中")
    status = db.Column(db.String(50), default="待跟进", index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class MatchRecord(db.Model):
    """撮合匹配表。"""

    __tablename__ = "match_records"

    id = db.Column(db.Integer, primary_key=True)
    demand_id = db.Column(
        db.Integer, db.ForeignKey("demands.id", ondelete="CASCADE"), nullable=False
    )
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"))
    match_score = db.Column(db.Numeric(5, 2))
    match_reason = db.Column(db.Text)
    risk_notes = db.Column(db.Text)
    recommendation_status = db.Column(db.String(50), default="未推荐", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class ProjectProgress(db.Model):
    """项目进展表。"""

    __tablename__ = "project_progress"

    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="SET NULL"), nullable=True
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"))
    foreign_client_id = db.Column(
        db.Integer, db.ForeignKey("foreign_clients.id", ondelete="SET NULL"), nullable=True
    )
    demand_id = db.Column(db.Integer, db.ForeignKey("demands.id", ondelete="SET NULL"))
    first_contact_date = db.Column(db.Date)
    material_sent_date = db.Column(db.Date)
    sample_status = db.Column(db.String(100))
    quotation_status = db.Column(db.String(100))
    negotiation_status = db.Column(db.String(100))
    contract_status = db.Column(db.String(100))
    deal_amount = db.Column(db.Numeric(18, 2))
    current_stage = db.Column(db.String(100), index=True)
    next_action = db.Column(db.Text)
    project_owner = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Document(db.Model):
    """文件归档表。"""

    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    enterprise_id = db.Column(
        db.Integer, db.ForeignKey("enterprises.id", ondelete="SET NULL"), nullable=True
    )
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete="SET NULL"))
    related_project_id = db.Column(
        db.Integer, db.ForeignKey("project_progress.id", ondelete="SET NULL")
    )
    document_type = db.Column(db.String(100), nullable=False, index=True)
    document_name = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(50), default="v1.0")
    file_path = db.Column(db.String(500), nullable=False)
    original_filename = db.Column(db.String(255))
    uploaded_by = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    notes = db.Column(db.Text)


class AuditLog(db.Model):
    """操作日志表。"""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(100), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
