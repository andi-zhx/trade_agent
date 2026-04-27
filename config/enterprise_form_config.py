"""企业入库表单（通用字段 + 行业专项字段）配置。"""

COMMON_ENTERPRISE_FIELD_GROUPS = [
    {
        "key": "A",
        "title": "A. 企业身份",
        "fields": [
            {"key": "company_full_name", "label": "企业全称", "type": "text", "required": True},
            {"key": "english_name", "label": "英文名称", "type": "text"},
            {"key": "unified_social_credit_code", "label": "统一社会信用代码", "type": "text"},
            {"key": "registered_address", "label": "注册地址", "type": "text"},
            {"key": "business_address", "label": "实际经营地址", "type": "text"},
            {"key": "founded_date", "label": "成立时间", "type": "date"},
            {"key": "registered_capital", "label": "注册资本", "type": "text"},
        ],
    },
    {
        "key": "B",
        "title": "B. 企业性质",
        "fields": [
            {
                "key": "enterprise_natures",
                "label": "企业性质（多选）",
                "type": "checkbox_group",
                "options": ["制造商", "贸易商", "品牌商", "代理商", "服务商", "OEM/ODM工厂"],
            }
        ],
    },
    {
        "key": "C",
        "title": "C. 联系信息",
        "fields": [
            {"key": "legal_person", "label": "法人", "type": "text"},
            {"key": "general_manager", "label": "总经理", "type": "text"},
            {"key": "trade_lead", "label": "外贸负责人", "type": "text"},
            {"key": "sales_lead", "label": "销售负责人", "type": "text"},
            {"key": "project_contact", "label": "项目对接人", "type": "text"},
            {"key": "contact_phone", "label": "电话", "type": "text"},
            {"key": "contact_email", "label": "邮箱", "type": "email"},
            {"key": "wechat", "label": "微信", "type": "text"},
            {"key": "website", "label": "官网", "type": "url"},
            {"key": "official_account", "label": "公众号", "type": "text"},
        ],
    },
    {
        "key": "D",
        "title": "D. 经营情况",
        "fields": [
            {"key": "main_business", "label": "主营业务", "type": "textarea"},
            {"key": "core_products", "label": "核心产品", "type": "textarea"},
            {"key": "annual_sales", "label": "年销售额", "type": "select", "options": ["500万以下", "500万-2000万", "2000万-5000万", "5000万-1亿", "1亿-5亿", "5亿以上", "暂未提供"]},
            {"key": "annual_exports", "label": "年出口额", "type": "select", "options": ["无出口", "100万以下", "100万-500万", "500万-2000万", "2000万-1亿", "1亿以上", "暂未提供"]},
            {"key": "major_clients", "label": "主要客户", "type": "textarea"},
            {"key": "major_markets", "label": "主要市场", "type": "textarea"},
        ],
    },
    {
        "key": "E",
        "title": "E. 生产能力",
        "fields": [
            {"key": "factory_area_range", "label": "厂房面积", "type": "select", "options": ["无自有工厂", "1000㎡以下", "1000-5000㎡", "5000-10000㎡", "1万-5万㎡", "5万㎡以上"]},
            {"key": "employee_count_range", "label": "员工数量", "type": "select", "options": ["20人以下", "20-50人", "50-100人", "100-300人", "300-1000人", "1000人以上"]},
            {"key": "production_line_count", "label": "产线数量", "type": "select", "options": ["无", "1-3条", "4-10条", "11-30条", "30条以上"]},
            {"key": "annual_capacity_level", "label": "年产能", "type": "select", "options": ["暂未提供", "小批量", "中等产能", "大规模产能", "可按订单扩产"]},
            {"key": "capacity_utilization", "label": "产能利用率", "type": "select", "options": ["50%以下", "50%-70%", "70%-90%", "90%以上", "暂未提供"]},
        ],
    },
    {
        "key": "F",
        "title": "F. 外贸能力",
        "fields": [
            {"key": "export_experience", "label": "是否有出口经验", "type": "select", "options": ["是", "否", "不确定"]},
            {"key": "export_countries", "label": "出口国家", "type": "textarea"},
            {"key": "forwarder_status", "label": "合作货代", "type": "select", "options": ["有固定货代", "无固定货代", "暂未提供"]},
            {"key": "trade_terms", "label": "常用贸易条款", "type": "checkbox_group", "options": ["EXW", "FOB", "CIF", "DDP", "DAP", "其他"]},
            {"key": "english_communication", "label": "是否能英文沟通", "type": "select", "options": ["可以", "部分可以", "不可以", "暂未确认"]},
        ],
    },
    {
        "key": "G",
        "title": "G. 财务信用",
        "fields": [
            {"key": "tax_certificate", "label": "纳税证明", "type": "select", "options": ["已提供", "未提供", "不适用"]},
            {"key": "credit_report", "label": "企业信用报告", "type": "select", "options": ["已提供", "未提供", "不适用"]},
            {"key": "litigation_status", "label": "涉诉情况", "type": "select", "options": ["无", "有", "待核查"]},
            {"key": "penalty_status", "label": "行政处罚情况", "type": "select", "options": ["无", "有", "待核查"]},
            {"key": "bank_credit_certificate", "label": "银行资信证明", "type": "select", "options": ["已提供", "未提供", "不适用"]},
        ],
    },
    {
        "key": "H",
        "title": "H. 合作意愿",
        "fields": [
            {"key": "target_countries", "label": "希望拓展国家", "type": "textarea"},
            {"key": "target_client_types", "label": "目标客户类型", "type": "checkbox_group", "options": ["进口商", "经销商", "品牌商", "工程商", "平台卖家", "政府采购", "终端客户", "其他"]},
            {"key": "cooperation_models", "label": "可接受合作模式", "type": "checkbox_group", "options": ["批发", "代理", "OEM", "ODM", "项目制", "跨境电商", "联合品牌", "其他"]},
            {"key": "minimum_order_quantity", "label": "最低订单量", "type": "text"},
            {"key": "price_flexibility", "label": "价格弹性", "type": "select", "options": ["强", "中", "弱", "暂未确认"]},
            {"key": "material_completeness", "label": "资料完整度", "type": "select", "options": ["A类资料完整", "B类资料较完整", "资料缺失较多", "待补充"]},
            {"key": "other_notes", "label": "其他说明", "type": "textarea"},
        ],
    },
]


from config.industry_config import INDUSTRY_EXTRA_FIELD_CONFIG
