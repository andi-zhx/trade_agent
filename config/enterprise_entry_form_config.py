"""企业新增/编辑表单配置（分模块）。

说明：
1. 本配置用于驱动企业录入页渲染，避免在 HTML 中硬编码大量字段。
2. 不破坏现有数据库结构：若字段无独立列，统一落库到 ``enterprise_extra_fields`` JSON。
3. 与现有数据兼容：字段名优先复用当前系统已在使用的 key。
"""

from __future__ import annotations

from copy import deepcopy

from config.industry_config import INDUSTRY_OPTIONS


MODULE_TITLES = {
    "0": "顶部固定区：入库信息",
    "A": "A. 企业身份",
    "B": "B. 企业性质与标签",
    "C": "C. 联系信息",
    "D": "D. 经营情况",
    "E": "E. 生产能力",
    "F": "F. 外贸能力",
    "G": "G. 财务信用",
    "H": "H. 资质合规",
    "I": "I. 项目判断与备注",
    "J": "J. 附件资料",
}

ENTRY_STATUS_OPTIONS = ["草稿", "待补充", "待审核", "已入库", "暂缓", "退出"]

SOURCE_CHANNEL_OPTIONS = [
    "主动报名",
    "政府推荐",
    "协会推荐",
    "展会获取",
    "老客户推荐",
    "网络收集",
    "其他",
]

ENTERPRISE_STAGE_OPTIONS = ["初步接触", "资料收集中", "已完成初审", "已推荐客户", "撮合中"]


def _field(
    field_name: str,
    label: str,
    field_type: str,
    required: bool,
    module: str,
    *,
    options: list | None = None,
    placeholder: str = "",
    help_text: str = "",
    show_when: dict | None = None,
    storage: str = "enterprise_extra_fields",
) -> dict:
    """构建统一字段配置。"""

    return {
        "field_name": field_name,
        "label": label,
        "type": field_type,
        "required": required,
        "options": options or [],
        "placeholder": placeholder,
        "help_text": help_text,
        "show_when": show_when,
        "module": module,
        # storage 兼容方案：
        # - column: 使用 enterprises 表中的既有列
        # - enterprise_extra_fields: 进入 JSON 扩展字段，避免改库
        "storage": storage,
    }


ENTERPRISE_ENTRY_FORM_MODULES = [
    {
        "module": "0",
        "title": MODULE_TITLES["0"],
        "fields": [
            _field(
                "enterprise_code",
                "企业编号",
                "auto",
                True,
                "0",
                storage="column",
                placeholder="保存后自动生成",
                help_text="格式示例：E2026-0001。新增记录时由系统生成，前端只读展示。",
            ),
            _field(
                "status",
                "入库状态",
                "select",
                True,
                "0",
                storage="column",
                options=ENTRY_STATUS_OPTIONS,
                placeholder="请选择入库状态",
            ),
            _field(
                "project_owner",
                "项目负责人",
                "select",
                True,
                "0",
                storage="column",
                options=[],
                placeholder="请选择项目负责人",
                help_text="建议运行时从系统用户列表加载；无用户时可回退固定选项。",
            ),
            _field(
                "source_channels",
                "资料来源",
                "checkbox_tags",
                True,
                "0",
                options=SOURCE_CHANNEL_OPTIONS,
                placeholder="可多选",
                help_text="若选择“其他”，建议在备注中补充具体来源。",
            ),
            _field(
                "industry_code",
                "行业大类",
                "select",
                True,
                "0",
                storage="column",
                options=[
                    {"value": item["code"], "label": f"{item['code']} {item['name']}"}
                    for item in INDUSTRY_OPTIONS
                ],
                placeholder="请选择行业大类",
                help_text="使用系统现有 20 个行业大类配置。",
            ),
            _field(
                "sub_industry",
                "细分行业",
                "select_or_text",
                False,
                "0",
                storage="column",
                options=[],
                placeholder="可选择或手动输入",
                help_text="根据行业大类联动；首期允许手动补充。",
                show_when={"field": "industry_code", "operator": "not_empty"},
            ),
            _field(
                "province",
                "省份",
                "select",
                True,
                "0",
                storage="column",
                options=[],
                placeholder="请选择省份",
            ),
            _field(
                "city",
                "城市",
                "select",
                True,
                "0",
                storage="column",
                options=[],
                placeholder="请先选择省份",
                show_when={"field": "province", "operator": "not_empty"},
            ),
            _field(
                "district",
                "区县",
                "select",
                False,
                "0",
                storage="column",
                options=[],
                placeholder="请先选择城市",
                show_when={"field": "city", "operator": "not_empty"},
            ),
            _field(
                "enterprise_stage",
                "企业当前阶段",
                "radio",
                False,
                "0",
                options=ENTERPRISE_STAGE_OPTIONS,
                placeholder="请选择当前阶段",
            ),
            _field(
                "enterprise_tag_notes",
                "企业标签备注",
                "text",
                False,
                "0",
                placeholder="补充企业标签、侧重点或识别结论",
            ),
        ],
    },
    {
        "module": "A",
        "title": MODULE_TITLES["A"],
        "fields": [
            _field(
                "company_full_name",
                "企业全称",
                "text",
                True,
                "A",
                placeholder="请输入营业执照上的企业全称",
            ),
            _field(
                "english_name",
                "企业英文名称",
                "text",
                False,
                "A",
                storage="column",
                placeholder="如有，请填写英文注册名称",
            ),
            _field(
                "company_short_name",
                "企业简称",
                "text",
                False,
                "A",
                placeholder="如有常用简称可填写",
            ),
            _field(
                "unified_social_credit_code",
                "统一社会信用代码",
                "text",
                True,
                "A",
                storage="column",
                placeholder="18位统一社会信用代码",
                help_text="格式提示：18位数字或大写字母组合。",
            ),
            _field(
                "founded_date",
                "成立时间",
                "date",
                True,
                "A",
                storage="column",
            ),
            _field(
                "registered_capital",
                "注册资本",
                "text",
                False,
                "A",
                storage="column",
                placeholder="保留原文，例如：1000万元人民币",
                help_text="保留企业原始表述，不做单位换算。",
            ),
            _field(
                "legal_representative",
                "法定代表人",
                "text",
                False,
                "A",
                placeholder="请输入法定代表人姓名",
            ),
            _field(
                "company_type",
                "企业主体类型",
                "radio",
                True,
                "A",
                storage="column",
                options=["内资", "外资", "合资", "港澳台", "其他"],
            ),
            _field(
                "enterprise_natures",
                "企业角色",
                "checkbox_tags",
                True,
                "A",
                options=["制造商", "贸易商", "品牌商", "服务商", "OEM工厂", "ODM工厂", "平台卖家"],
            ),
            _field(
                "is_independent_legal_entity",
                "是否独立法人",
                "radio",
                False,
                "A",
                options=["是", "否", "未知"],
            ),
            _field(
                "is_listed_or_pre_ipo",
                "是否上市",
                "radio",
                False,
                "A",
                storage="column",
                options=["是", "否"],
            ),
            _field(
                "listing_location",
                "上市地点",
                "select",
                False,
                "A",
                options=["A股", "港股", "美股", "其他"],
                show_when={"field": "is_listed_or_pre_ipo", "operator": "equals", "value": "是"},
            ),
            _field(
                "stock_code",
                "股票代码",
                "text",
                False,
                "A",
                placeholder="请输入股票代码",
                show_when={"field": "is_listed_or_pre_ipo", "operator": "equals", "value": "是"},
            ),
            _field(
                "registered_address",
                "注册地址",
                "text",
                False,
                "A",
                storage="column",
            ),
            _field(
                "business_address",
                "实际经营地址",
                "text",
                False,
                "A",
                storage="column",
            ),
            _field(
                "office_factory_address_consistency",
                "办公地址与工厂是否一致",
                "radio",
                False,
                "A",
                options=["一致", "不一致", "未核验"],
            ),
        ],
    },
    {
        "module": "B",
        "title": MODULE_TITLES["B"],
        "fields": [
            _field(
                "ownership_type",
                "企业所有制性质",
                "radio",
                False,
                "B",
                options=["国企", "民企", "外资", "合资", "集体", "其他"],
            ),
            _field(
                "enterprise_scale",
                "企业规模",
                "radio",
                False,
                "B",
                options=["微型", "小型", "中型", "大型", "未知"],
            ),
            _field(
                "employee_count_range",
                "员工规模",
                "radio",
                False,
                "B",
                options=["1-20", "21-50", "51-100", "101-300", "301-500", "500+"],
            ),
            _field(
                "enterprise_development_stage",
                "企业发展阶段",
                "radio",
                False,
                "B",
                options=["初创", "成长期", "成熟期", "稳定经营", "转型期"],
            ),
            _field(
                "is_high_tech",
                "是否高新技术企业",
                "radio",
                False,
                "B",
                storage="column",
                options=["是", "否", "未知"],
            ),
            _field(
                "is_specialized_new",
                "是否专精特新",
                "radio",
                False,
                "B",
                storage="column",
                options=["国家级小巨人", "省级专精特新", "市级", "否", "未知"],
            ),
            _field(
                "is_tech_sme",
                "是否科技型中小企业",
                "radio",
                False,
                "B",
                options=["是", "否", "未知"],
            ),
            _field(
                "has_own_brand",
                "是否有自有品牌",
                "radio",
                False,
                "B",
                options=["是", "否"],
            ),
            _field(
                "brand_name",
                "品牌名称",
                "text",
                False,
                "B",
                show_when={"field": "has_own_brand", "operator": "equals", "value": "是"},
            ),
            _field(
                "brand_types",
                "品牌类型",
                "checkbox_tags",
                False,
                "B",
                options=["国内品牌", "出口品牌", "跨境品牌", "OEM代工为主"],
                help_text="仅在企业有自有品牌时重点填写。",
                show_when={"field": "has_own_brand", "operator": "equals", "value": "是"},
            ),
            _field(
                "business_models",
                "经营模式",
                "checkbox_tags",
                False,
                "B",
                options=["自产自销", "贸易分销", "OEM", "ODM", "工程项目", "跨境电商", "服务交付"],
            ),
            _field(
                "enterprise_advantage_tags",
                "企业优势标签",
                "checkbox_tags",
                False,
                "B",
                options=[
                    "价格优势",
                    "质量稳定",
                    "快速交付",
                    "小单灵活",
                    "定制能力强",
                    "研发能力强",
                    "海外经验丰富",
                    "渠道资源强",
                ],
            ),
            _field(
                "is_key_recommended_enterprise",
                "是否重点推荐企业",
                "radio",
                False,
                "B",
                options=["是", "否", "待定"],
            ),
        ],
    },
    {"module": "C", "title": MODULE_TITLES["C"], "fields": []},
    {"module": "D", "title": MODULE_TITLES["D"], "fields": []},
    {"module": "E", "title": MODULE_TITLES["E"], "fields": []},
    {"module": "F", "title": MODULE_TITLES["F"], "fields": []},
    {"module": "G", "title": MODULE_TITLES["G"], "fields": []},
    {"module": "H", "title": MODULE_TITLES["H"], "fields": []},
    {"module": "I", "title": MODULE_TITLES["I"], "fields": []},
    {"module": "J", "title": MODULE_TITLES["J"], "fields": []},
]


def get_enterprise_entry_form_modules() -> list[dict]:
    """返回企业录入表单模块配置副本，避免被调用方就地修改。"""

    return deepcopy(ENTERPRISE_ENTRY_FORM_MODULES)


def get_enterprise_entry_top_fields() -> list[dict]:
    """返回顶部固定区字段配置。"""

    for module in ENTERPRISE_ENTRY_FORM_MODULES:
        if module["module"] == "0":
            return deepcopy(module["fields"])
    return []
