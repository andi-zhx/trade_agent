"""企业资料分层加权完整度计算工具。"""

from datetime import date, datetime
from decimal import Decimal

from config.enterprise_form_config import COMMON_ENTERPRISE_FIELD_GROUPS, INDUSTRY_EXTRA_FIELD_CONFIG

MODULE_BASE_WEIGHTS = {
    "basic": 40,
    "business": 20,
    "export": 20,
    "documents": 10,
    "industry": 10,
}

MODULE_LABELS = {
    "basic": "基础入库信息",
    "business": "工商与经营信息",
    "export": "外贸与出海能力",
    "documents": "附件资料",
    "industry": "行业专项信息",
}

DOCUMENT_TYPE_WEIGHTS = {
    "营业执照": 4,
    "企业介绍": 2,
    "BP/融资材料": 1,
    "工厂照片": 1,
    "资质荣誉": 1,
    "财务/经营资料": 1,
    "其他": 0.5,
}

MODULE_FIELD_CANDIDATES = {
    "basic": [
        "enterprise_code",
        "project_owner",
        "industry_code",
        "industry_category",
        "company_full_name",
        "registered_name",
        "province",
        "city",
        "sub_industry",
        "primary_contact_name",
        "primary_contact_mobile",
        "contact_phone",
        "contact_email",
        "dynamic_contacts",
    ],
    "business": [
        "unified_social_credit_code",
        "company_type",
        "legal_representative",
        "registered_capital",
        "founded_date",
        "business_term_start",
        "business_scope",
        "employee_count_range",
        "annual_revenue_range",
        "factory_area_range",
        "production_line_count",
        "business_directions",
        "enterprise_description",
    ],
    "export": [
        "has_import_export_qualification",
        "has_overseas_business",
        "major_export_regions",
        "export_experience",
        "customer_types",
        "certificate_completeness",
        "target_expansion_markets",
        "foreign_trade_support_needs",
        "foreign_trade_team_size",
        "attended_international_expo",
        "cross_border_platforms",
        "export_docs_familiarity",
    ],
}

FIELD_ALIASES = {
    "industry_category": ["industry_category", "industry"],
    "company_full_name": ["company_full_name", "company_name"],
    "registered_name": ["registered_name", "company_full_name", "company_name"],
    "primary_contact_mobile": ["primary_contact_mobile", "contact_mobile", "mobile"],
    "contact_email": ["contact_email", "email"],
    "contact_phone": ["contact_phone", "phone"],
    "employee_count_range": ["employee_count_range", "employee_scale", "employee_count"],
    "annual_revenue_range": ["annual_revenue_range", "revenue_scale", "annual_sales", "annual_revenue"],
    "factory_area_range": ["factory_area_range", "factory_area"],
    "production_line_count": ["production_line_count", "production_capacity", "annual_capacity"],
    "business_directions": ["business_directions", "main_business", "main_business_direction"],
    "enterprise_description": ["enterprise_description", "company_profile", "main_business"],
    "has_overseas_business": ["has_overseas_business", "export_suitability"],
    "major_export_regions": ["major_export_regions", "export_countries"],
    "customer_types": ["customer_types", "overseas_customers"],
    "certificate_completeness": ["certificate_completeness", "certification_status"],
    "target_expansion_markets": ["target_expansion_markets", "target_market", "target_countries", "target_markets"],
    "foreign_trade_support_needs": ["foreign_trade_support_needs", "cooperation_needs", "cooperation_preferences"],
    "foreign_trade_team_size": ["foreign_trade_team_size", "foreign_trade_team"],
    "attended_international_expo": ["attended_international_expo", "exhibition_experience"],
    "cross_border_platforms": ["cross_border_platforms", "overseas_channel", "sales_channels"],
}


def is_filled_value(value, field_type=None):
    """按表单控件语义判断字段是否已填写。"""

    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set)):
        return any(is_filled_value(item) for item in value)
    if isinstance(value, dict):
        return any(is_filled_value(item) for item in value.values())
    if isinstance(value, (date, datetime, Decimal, int, float, bool)):
        return True
    return True


def is_dynamic_contacts_filled(value):
    if not isinstance(value, list):
        return False
    for row in value:
        if not isinstance(row, dict):
            continue
        if is_filled_value(row.get("name")) or is_filled_value(row.get("mobile")):
            return True
    return False


def collect_enterprise_field_definitions(industry_code=None):
    """收集当前企业表单实际配置字段，包含通用字段和当前行业专项字段。"""

    definitions = {}
    for group in COMMON_ENTERPRISE_FIELD_GROUPS:
        for field in group.get("fields", []):
            key = field.get("key")
            if key:
                definitions[key] = dict(field)
    for group in INDUSTRY_EXTRA_FIELD_CONFIG.get((industry_code or "").strip(), []):
        for field in group.get("fields", []):
            key = field.get("key")
            if key:
                definitions[key] = dict(field)
    return definitions


def get_field_label_map(industry_code=None):
    labels = {key: field.get("label") or key for key, field in collect_enterprise_field_definitions(industry_code).items()}
    labels.update({
        "industry_category": labels.get("industry_code", "行业分类"),
        "employee_count": labels.get("employee_count_range", "人员规模"),
        "annual_revenue": labels.get("annual_revenue_range", "年营业收入区间"),
        "target_markets": labels.get("target_expansion_markets", "拟拓展市场"),
        "export_countries": labels.get("major_export_regions", "主要出口区域"),
        "main_business": labels.get("business_directions", "主营业务方向"),
    })
    return labels


def _enterprise_value(enterprise, key):
    if not enterprise:
        return None
    if hasattr(enterprise, key):
        return getattr(enterprise, key)
    return None


def _get_extra(enterprise):
    if not enterprise:
        return {}
    extra = getattr(enterprise, "enterprise_extra_fields", None) or {}
    return dict(extra) if isinstance(extra, dict) else {}


def _field_value(enterprise, extra, key):
    aliases = FIELD_ALIASES.get(key, [key])
    for alias in aliases:
        value = extra.get(alias)
        if is_filled_value(value):
            return value
        value = _enterprise_value(enterprise, alias)
        if is_filled_value(value):
            return value
    return extra.get(key) if key in extra else _enterprise_value(enterprise, key)


def _configured_candidate_keys(module_key, field_definitions, enterprise):
    keys = []
    for key in MODULE_FIELD_CANDIDATES[module_key]:
        aliases = FIELD_ALIASES.get(key, [key])
        if key in field_definitions or any(alias in field_definitions or hasattr(enterprise, alias) for alias in aliases):
            keys.append(key)
    return keys


def _calculate_field_module(enterprise, extra, module_key, keys, labels, field_definitions, weight):
    done = 0
    missing = []
    for key in keys:
        field_type = (field_definitions.get(key) or {}).get("type")
        value = _field_value(enterprise, extra, key)
        filled = is_dynamic_contacts_filled(value) if key == "dynamic_contacts" else is_filled_value(value, field_type)
        if filled:
            done += 1
        else:
            missing.append(labels.get(key) or key)
    total = len(keys)
    score = int(round(done / total * 100)) if total else 100
    return {
        "label": MODULE_LABELS[module_key],
        "score": max(0, min(100, score)),
        "weight": weight,
        "done": done,
        "total": total,
        "missing_fields": missing,
    }


def _document_types_from_documents(documents):
    if documents is None:
        return set()
    types = set()
    for item in documents:
        if isinstance(item, str):
            doc_type = item
        elif isinstance(item, dict):
            doc_type = item.get("document_type")
        else:
            doc_type = getattr(item, "document_type", None)
        if is_filled_value(doc_type):
            types.add(str(doc_type).strip())
    return types


def calculate_document_completeness(documents=None, weight=MODULE_BASE_WEIGHTS["documents"]):
    covered_types = _document_types_from_documents(documents)
    done_points = sum(points for doc_type, points in DOCUMENT_TYPE_WEIGHTS.items() if doc_type in covered_types)
    total_points = sum(DOCUMENT_TYPE_WEIGHTS.values())
    score = int(round(done_points / total_points * 100)) if total_points else 0
    missing = [doc_type for doc_type in DOCUMENT_TYPE_WEIGHTS if doc_type not in covered_types]
    return {
        "label": MODULE_LABELS["documents"],
        "score": max(0, min(100, score)),
        "weight": weight,
        "done": done_points,
        "total": total_points,
        "missing_fields": missing,
    }


def _effective_weights(has_industry_fields):
    weights = dict(MODULE_BASE_WEIGHTS)
    if has_industry_fields:
        return weights
    industry_weight = weights.pop("industry")
    base_total = sum(weights.values())
    for key in list(weights):
        weights[key] = round(weights[key] + industry_weight * weights[key] / base_total, 1)
    weights["industry"] = 0
    return weights


def calculate_enterprise_material_completeness(enterprise, documents=None):
    """计算企业资料分层加权完整度，返回总分、标签和各模块明细。"""

    extra = _get_extra(enterprise)
    industry_code = (extra.get("industry_code") or _enterprise_value(enterprise, "industry_code") or "").strip()
    field_definitions = collect_enterprise_field_definitions(industry_code)
    labels = get_field_label_map(industry_code)
    industry_groups = INDUSTRY_EXTRA_FIELD_CONFIG.get(industry_code, [])
    industry_keys = [field.get("key") for group in industry_groups for field in group.get("fields", []) if field.get("key")]
    weights = _effective_weights(bool(industry_keys))

    modules = {}
    for module_key in ("basic", "business", "export"):
        keys = _configured_candidate_keys(module_key, field_definitions, enterprise)
        modules[module_key] = _calculate_field_module(
            enterprise, extra, module_key, keys, labels, field_definitions, weights[module_key]
        )
    modules["documents"] = calculate_document_completeness(documents, weights["documents"])
    modules["industry"] = _calculate_field_module(
        enterprise, extra, "industry", industry_keys, labels, field_definitions, weights["industry"]
    )
    if not industry_keys:
        modules["industry"]["score"] = 100
        modules["industry"]["missing_fields"] = []

    total_score = int(round(sum(module["score"] * module["weight"] / 100 for module in modules.values())))
    total_score = max(0, min(100, total_score))
    missing_fields = []
    for module in modules.values():
        missing_fields.extend(module.get("missing_fields", []))

    return {
        "total_score": total_score,
        "total_label": f"{total_score}%",
        "score": total_score,
        "label": f"{total_score}%",
        "color": "success" if total_score >= 80 else ("warning" if total_score >= 50 else "danger"),
        "missing_fields": missing_fields,
        "missing_items": missing_fields,
        "modules": modules,
        "suggestions": missing_fields[:5],
    }
