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
    {"module": "A", "title": MODULE_TITLES["A"], "fields": []},
    {"module": "B", "title": MODULE_TITLES["B"], "fields": []},
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
