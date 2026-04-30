#!/usr/bin/env python3
"""按“企业导入模板 / 产品导入模板”语义生成样例数据并写入 SQLite 数据库。

执行：python generate_sample_data.py
效果：
- 写入 trade_agent.db（enterprises / products）
- 不生成 CSV 文件
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from app import create_app
from models import Enterprise, Product, db

ENTERPRISE_COUNT = 50
PRODUCTS_PER_ENTERPRISE = 5

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
PRODUCT_TYPES = ["标准品", "定制品", "OEM", "ODM"]
MARKETS = ["东南亚", "中东", "欧洲", "北美", "拉美", "非洲"]


def random_date(start_year: int = 2008, end_year: int = 2025) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def build_enterprise(i: int) -> Enterprise:
    province = random.choice(PROVINCES)
    city = random.choice(CITIES[province])
    industry = random.choice(INDUSTRY_NAMES)
    has_export = random.choice([True, False])
    code = f"ENT-{20260430 + (i // 100):08d}-{i:03d}"

    extra_fields = {
        "company_full_name": f"样例企业{i:03d}有限公司",
        "annual_sales": random.choice(["500万以下", "500万-2000万", "2000万-1亿", "1亿-5亿"]),
        "annual_exports": random.choice(["无", "100万以下", "100万-1000万", "1000万-1亿"]),
        "production_line_count": random.choice(["1-5条", "6-10条", "11-20条"]),
    }

    return Enterprise(
        enterprise_code=code,
        company_name=extra_fields["company_full_name"],
        english_name=f"Sample Enterprise {i:03d} Co., Ltd.",
        unified_social_credit_code=f"91310000MA{i:010d}"[-18:],
        province=province,
        city=city,
        industry_category=industry,
        main_products=random.choice(["工业传感器、控制模块", "智能终端、连接器", "电源模块、执行器"]),
        employee_count=random.randint(30, 1200),
        factory_area=random.choice(["3000㎡", "6000㎡", "12000㎡", "20000㎡"]),
        has_foreign_trade_experience=has_export,
        enterprise_extra_fields=extra_fields,
        status="active",
    )


def build_product(ent: Enterprise, idx: int) -> Product:
    quote_date = random_date(2024, 2026)
    return Product(
        enterprise_id=ent.id,
        product_code=f"PRD-{ent.id:04d}-{idx:03d}",
        product_name_cn=f"{ent.company_name.replace('有限公司', '')}产品{idx}",
        product_name_en=f"Product {idx} of {ent.enterprise_code}",
        industry_name=ent.industry_category,
        product_category=random.choice(PRODUCT_CATEGORIES),
        product_type=random.choice(PRODUCT_TYPES),
        hs_code=str(random.randint(1000000000, 9999999999)),
        moq=str(random.choice(["10", "100", "500", "1000"])),
        delivery_cycle=random.choice(["7天", "15天", "30天"]),
        price_display=random.choice(["USD 8-12", "USD 18-22", "USD 35-48"]),
        target_market="、".join(random.sample(MARKETS, k=2)),
        export_suitability=random.choice(["适合", "基本适合", "待判断"]),
        recommendation_level=random.choice(["A优先推荐", "B可推荐", "C待完善"]),
        certification_status=random.choice(["齐全", "部分齐全", "待补充"]),
        quote_date=quote_date,
        quote_valid_until=quote_date + timedelta(days=90),
        status="active",
        product_extra_fields={"product_status_review": random.choice(["已入库", "待补充", "已推荐"])},
        notes="由脚本自动生成，用于导入模板联调",
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

        product_total = 0
        for ent in enterprises:
            for i in range(1, PRODUCTS_PER_ENTERPRISE + 1):
                db.session.add(build_product(ent, i))
                product_total += 1

        db.session.commit()
        print(f"已写入企业样例数据: {len(enterprises)} 条")
        print(f"已写入产品样例数据: {product_total} 条")
        print("写入位置: trade_agent.db")


if __name__ == "__main__":
    main()
