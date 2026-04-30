#!/usr/bin/env python3
"""根据当前 SQLAlchemy 数据结构生成样例数据并写入 SQLite 数据库。"""

from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from app import create_app
from models import Enterprise, Product, ProductSKU, db

ENTERPRISE_COUNT = 50
PRODUCTS_PER_ENTERPRISE = 5
SKUS_PER_PRODUCT = 3

PROVINCES = ["广东省", "浙江省", "江苏省", "山东省", "福建省", "上海市", "北京市"]
CITIES = {
    "广东省": ["深圳市", "广州市", "东莞市", "佛山市"],
    "浙江省": ["杭州市", "宁波市", "温州市", "绍兴市"],
    "江苏省": ["苏州市", "南京市", "无锡市", "常州市"],
    "山东省": ["青岛市", "济南市", "烟台市", "潍坊市"],
    "福建省": ["厦门市", "福州市", "泉州市", "漳州市"],
    "上海市": ["上海市"],
    "北京市": ["北京市"],
}
INDUSTRY_NAMES = ["电子信息", "纺织服装", "机械装备", "家居日用", "食品饮料"]
PRODUCT_CATEGORIES = ["工业传感器", "控制模块", "智能终端", "配套部件"]
MARKETS = ["东南亚", "中东", "欧洲", "北美", "拉美", "非洲"]
COUNTRIES = ["越南", "泰国", "阿联酋", "德国", "美国", "巴西"]


def random_date(start_year: int = 2008, end_year: int = 2025) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def build_enterprise(i: int) -> Enterprise:
    province = random.choice(PROVINCES)
    city = random.choice(CITIES[province])
    industry = random.choice(INDUSTRY_NAMES)
    founded = random_date(2005, 2022)

    annual_revenue = Decimal(str(random.choice([1200, 3500, 6800, 12000, 25000])))
    export_revenue = Decimal(str(random.choice([300, 1200, 2600, 5000, 11000])))

    return Enterprise(
        enterprise_code=f"ENT-2026-{i:04d}",
        company_name=f"样例企业{i:03d}有限公司",
        english_name=f"Sample Enterprise {i:03d} Co., Ltd.",
        unified_social_credit_code=f"91310000MA{i:010d}"[-18:],
        founded_date=founded,
        registered_capital=random.choice(["500万人民币", "1000万人民币", "3000万人民币"]),
        registered_address=f"{province}{city}高新园区{random.randint(1,99)}号",
        business_address=f"{province}{city}产业路{random.randint(1,99)}号",
        province=province,
        city=city,
        district=random.choice(["南山区", "高新区", "开发区", "工业园"]),
        company_type=random.choice(["有限责任公司", "股份有限公司"]),
        industry_code=f"I{random.randint(10, 99)}",
        industry_category=industry,
        sub_industry=random.choice(["核心零部件", "系统集成", "消费品制造"]),
        main_products=random.choice(["工业传感器、控制模块", "智能终端、连接器", "电源模块、执行器"]),
        main_business="研发、生产与销售，支持ODM/OEM合作",
        is_manufacturer=True,
        is_trader=random.choice([True, False]),
        is_brand_owner=random.choice([True, False]),
        is_oem_odm=random.choice([True, False]),
        is_service_provider=random.choice([False, True]),
        is_high_tech=random.choice([True, False]),
        is_specialized_new=random.choice([True, False]),
        is_listed_or_pre_ipo=random.choice([True, False]),
        has_foreign_trade_experience=random.choice([True, False]),
        export_countries="、".join(random.sample(COUNTRIES, k=3)),
        target_markets="、".join(random.sample(MARKETS, k=2)),
        annual_capacity=random.choice(["10万件", "50万件", "100万件"]),
        employee_count=random.randint(30, 1200),
        factory_area=random.choice(["3000㎡", "6000㎡", "12000㎡", "20000㎡"]),
        main_equipment="SMT产线、注塑机、自动测试设备",
        annual_revenue=annual_revenue,
        export_revenue=export_revenue,
        service_needs="海外市场拓展、合规认证支持",
        risk_notes=random.choice(["", "需补充部分认证", "汇率波动敏感"]),
        enterprise_extra_fields={"source": "sample_script", "score": random.randint(60, 95)},
        status="active",
        project_owner=random.choice(["Alice", "Bob", "Carol", "David"]),
    )


def build_product(ent: Enterprise, idx: int) -> Product:
    ptype = random.choice(Product.PRODUCT_TYPE_OPTIONS)
    return Product(
        enterprise_id=ent.id,
        product_code=f"PRD-{ent.id:04d}-{idx:03d}",
        product_name_cn=f"{ent.company_name.replace('有限公司', '')}产品{idx}",
        product_name_en=f"Product {idx} of {ent.enterprise_code}",
        industry_code=ent.industry_code,
        industry_name=ent.industry_category,
        product_category=random.choice(PRODUCT_CATEGORIES),
        product_type=ptype,
        hs_code=str(random.randint(100000, 999999)),
        function_description="具备高稳定性与低功耗特点，适用于工业与消费场景。",
        application_scenario=random.choice(["智能制造", "楼宇自动化", "消费电子", "能源监测"]),
        target_market="、".join(random.sample(MARKETS, k=2)),
        export_suitability=random.choice(Product.EXPORT_SUITABILITY_OPTIONS),
        recommendation_level=random.choice(Product.RECOMMENDATION_LEVEL_OPTIONS),
        existing_sales_countries="、".join(random.sample(COUNTRIES, k=2)),
        certifications=random.choice(["CE, RoHS", "FCC", "ISO9001", "暂无"]),
        certification_status=random.choice(Product.CERTIFICATION_STATUS_OPTIONS),
        product_selling_points="交付快、支持定制、性价比高",
        notes="由脚本自动生成，用于联调和展示",
        product_extra_fields={"stage": "已入库", "material_ready": random.choice(["是", "否"])},
        status="active",
    )


def build_sku(product: Product, idx: int) -> ProductSKU:
    return ProductSKU(
        product_id=product.id,
        sku_code=f"SKU-{product.id:05d}-{idx:03d}",
        sku_name=f"{product.product_name_cn}-规格{idx}",
        model=f"M{random.randint(100,999)}",
        specification=random.choice(["220V/50Hz", "110V/60Hz", "IP65", "Class II"]),
        color=random.choice(["黑色", "白色", "银色"]),
        size=random.choice(["S", "M", "L"]),
        material=random.choice(["铝合金", "ABS", "不锈钢"]),
        unit="pcs",
        package_spec=random.choice(["10pcs/箱", "20pcs/箱", "50pcs/箱"]),
        moq=random.choice(["10", "50", "100"]),
        price=Decimal(str(random.choice([8.8, 15.5, 23.9, 39.0]))),
        gross_weight=random.choice(["1.2kg", "2.5kg", "3.1kg"]),
        net_weight=random.choice(["1.0kg", "2.1kg", "2.8kg"]),
        delivery_cycle=random.choice(["7天", "15天", "30天"]),
        currency="USD",
        customization_supported=random.choice([True, False]),
        notes="样例SKU",
    )


def main() -> None:
    random.seed(20260430)
    app = create_app()
    with app.app_context():
        db.create_all()

        enterprises: list[Enterprise] = []
        for i in range(1, ENTERPRISE_COUNT + 1):
            ent = build_enterprise(i)
            db.session.add(ent)
            enterprises.append(ent)
        db.session.flush()

        products: list[Product] = []
        for ent in enterprises:
            for i in range(1, PRODUCTS_PER_ENTERPRISE + 1):
                product = build_product(ent, i)
                db.session.add(product)
                products.append(product)
        db.session.flush()

        sku_total = 0
        for product in products:
            for i in range(1, SKUS_PER_PRODUCT + 1):
                db.session.add(build_sku(product, i))
                sku_total += 1

        db.session.commit()
        print(f"已写入企业样例数据: {len(enterprises)} 条")
        print(f"已写入产品样例数据: {len(products)} 条")
        print(f"已写入SKU样例数据: {sku_total} 条")
        print("写入位置: trade_agent.db")


if __name__ == "__main__":
    main()
