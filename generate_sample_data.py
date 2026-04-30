#!/usr/bin/env python3
"""生成企业与产品样例数据。

执行：python generate_sample_data.py
输出：
- sample_data/enterprises.csv （50 条企业）
- sample_data/products.csv （每家企业 5 条产品，共 250 条）
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ENTERPRISE_COUNT = 50
PRODUCTS_PER_ENTERPRISE = 5
OUTPUT_DIR = Path("sample_data")

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
INDUSTRIES = [
    ("ELEC", "电子电气"),
    ("TEXT", "纺织服装"),
    ("MACH", "机械设备"),
    ("HOME", "家居日用"),
    ("FOOD", "食品饮料"),
]
PRODUCT_CATEGORIES = ["核心产品", "配套产品", "升级产品", "定制产品"]
PRODUCT_TYPES = ["标准品", "定制品", "OEM", "ODM"]
MARKETS = ["东南亚", "中东", "欧洲", "北美", "拉美", "非洲"]


def random_date(start_year: int = 2005, end_year: int = 2024) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_enterprise_rows(count: int) -> list[dict]:
    rows = []
    for i in range(1, count + 1):
        code = f"ENT{i:04d}"
        province = random.choice(PROVINCES)
        city = random.choice(CITIES[province])
        industry_code, industry_name = random.choice(INDUSTRIES)
        founded = random_date()
        row = {
            "enterprise_code": code,
            "company_name": f"样例企业{i:03d}有限公司",
            "english_name": f"Sample Enterprise {i:03d} Co., Ltd.",
            "province": province,
            "city": city,
            "industry_code": industry_code,
            "industry_category": industry_name,
            "founded_date": founded.isoformat(),
            "employee_count": random.randint(20, 1500),
            "annual_revenue": f"{random.randint(500, 50000) * 10000:.2f}",
            "has_foreign_trade_experience": random.choice(["True", "False"]),
            "target_markets": ",".join(random.sample(MARKETS, k=2)),
            "status": random.choice(["draft", "active", "archived"]),
        }
        rows.append(row)
    return rows


def generate_product_rows(enterprises: list[dict], per_enterprise: int) -> list[dict]:
    rows = []
    product_index = 1
    for ent in enterprises:
        for p in range(1, per_enterprise + 1):
            quote_date = random_date(2023, 2025)
            valid_until = quote_date + timedelta(days=90)
            row = {
                "product_code": f"PRD{product_index:05d}",
                "enterprise_code": ent["enterprise_code"],
                "product_name_cn": f"{ent['company_name'].replace('有限公司', '')}产品{p}",
                "product_name_en": f"Product {p} of {ent['enterprise_code']}",
                "industry_code": ent["industry_code"],
                "industry_name": ent["industry_category"],
                "product_category": random.choice(PRODUCT_CATEGORIES),
                "product_type": random.choice(PRODUCT_TYPES),
                "hs_code": str(random.randint(10000000, 99999999)),
                "unit": random.choice(["件", "台", "套", "箱"]),
                "moq": str(random.choice([50, 100, 200, 500])),
                "exw_price": f"{random.uniform(5, 300):.2f}",
                "currency": "USD",
                "quote_date": quote_date.isoformat(),
                "quote_valid_until": valid_until.isoformat(),
                "target_market": random.choice(MARKETS),
                "export_suitability": random.choice(["适合", "基本适合", "待判断"]),
                "recommendation_level": random.choice(["A优先推荐", "B可推荐", "C待完善"]),
                "certification_status": random.choice(["齐全", "部分齐全", "待补充"]),
                "status": random.choice(["active", "draft", "inactive"]),
            }
            rows.append(row)
            product_index += 1
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    random.seed(20260430)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    enterprises = generate_enterprise_rows(ENTERPRISE_COUNT)
    products = generate_product_rows(enterprises, PRODUCTS_PER_ENTERPRISE)

    enterprise_file = OUTPUT_DIR / "enterprises.csv"
    product_file = OUTPUT_DIR / "products.csv"

    write_csv(enterprise_file, enterprises)
    write_csv(product_file, products)

    print(f"企业数据已生成: {enterprise_file} ({len(enterprises)} 条)")
    print(f"产品数据已生成: {product_file} ({len(products)} 条)")


if __name__ == "__main__":
    main()
