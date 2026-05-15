"""行业配置中心：统一维护行业分类、覆盖范围、行业专项字段及审核要点。"""


INDUSTRY_NAMES = [
    "汽车及零部件",
    "电力、电缆、能源、环保",
    "劳保、安防、应急",
    "五金、建材、紧固件、电梯、园艺",
    "塑料",
    "化工",
    "服装服饰",
    "面料辅料、无纺布、纱线、家纺",
    "工业、机械",
    "医疗",
    "零售消费",
    "畜牧",
    "游戏动漫",
    "孕婴童",
    "二轮车",
    "低空",
    "数据科技",
    "境外自办展",
]


def _industry_config_item(name):
    """构建仅使用行业名称的行业配置项。"""

    return {
        "code": name,
        "name": name,
        "scope": name,
        "enterprise": {
            "key": f"{name}企业专项",
            "title": f"{name}专项",
            "fields": [],
        },
        "product": {
            "key": f"{name}产品专项",
            "title": f"{name}专项",
            "fields": [],
        },
        "focus_qualifications": [],
        "focus_questions": [],
    }


INDUSTRY_CONFIG = {name: _industry_config_item(name) for name in INDUSTRY_NAMES}

INDUSTRY_OPTIONS = [
    {"code": item["code"], "name": item["name"], "scope": item["scope"]}
    for item in INDUSTRY_CONFIG.values()
]

INDUSTRY_MAP = {item["code"]: item for item in INDUSTRY_OPTIONS}

INDUSTRY_EXTRA_FIELD_CONFIG = {
    code: [industry["enterprise"]]
    for code, industry in INDUSTRY_CONFIG.items()
}

INDUSTRY_PRODUCT_EXTRA_FIELD_CONFIG = {
    code: [industry["product"]]
    for code, industry in INDUSTRY_CONFIG.items()
}
