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


def _industry_fields(*labels):
    return [{"key": f"f{idx}", "label": label, "type": "textarea" if "经验" in label or "案例" in label else "text"} for idx, label in enumerate(labels, start=1)]


INDUSTRY_EXTRA_FIELD_CONFIG = {
    "I01": [{"key": "I01A", "title": "工业机械专项", "fields": _industry_fields("设备加工能力", "装配能力", "调试能力", "研发团队人数", "已交付设备案例", "海外项目经验", "售后备件能力")}],
    "I02": [{"key": "I02A", "title": "电子电器专项", "fields": _industry_fields("硬件研发能力", "软件研发能力", "SMT产线", "老化测试线", "芯片供应链", "品牌代工经验")}],
    "I03": [{"key": "I03A", "title": "电力能源专项", "fields": _industry_fields("高低压设备能力", "电缆制造能力", "变配电成套经验", "并网项目经验", "关键认证资质", "海外电力标准适配")}],
    "I04": [{"key": "I04A", "title": "新能源环保专项", "fields": _industry_fields("光储系统集成能力", "节能解决方案能力", "环保处理工艺", "碳排管理能力", "新能源项目案例", "海外运维服务能力")}],
    "I05": [{"key": "I05A", "title": "汽车摩托专项", "fields": _industry_fields("整车/零部件开发能力", "IATF16949体系", "关键零部件测试能力", "主机厂配套经验", "售后备件供应能力", "海外认证经验")}],
    "I06": [{"key": "I06A", "title": "低空经济专项", "fields": _industry_fields("飞控系统能力", "机体结构设计能力", "任务载荷集成能力", "试飞测试能力", "适航/合规准备情况", "海外项目经验")}],
    "I07": [{"key": "I07A", "title": "五金建材专项", "fields": _industry_fields("材料加工能力", "工程配套能力", "防火/防水标准能力", "施工交付经验", "大型项目案例", "现场服务能力")}],
    "I08": [{"key": "I08A", "title": "化工新材料专项", "fields": _industry_fields("核心配方能力", "中试放大能力", "危险品合规能力", "MSDS与REACH准备", "稳定供货能力", "海外法规符合性")}],
    "I09": [{"key": "I09A", "title": "纺织家纺专项", "fields": _industry_fields("织造染整能力", "面辅料开发能力", "打样反应速度", "质量检验体系", "快返单能力", "国际品牌供货经验")}],
    "I10": [{"key": "I10A", "title": "服饰鞋帽专项", "fields": _industry_fields("版型开发能力", "柔性生产能力", "鞋包打样能力", "时尚趋势响应能力", "品牌合作经验", "可持续材料应用")}],
    "I11": [{"key": "I11A", "title": "家居家具专项", "fields": _industry_fields("家具结构设计能力", "板木金工艺能力", "整装配套能力", "包装抗损能力", "海外仓配经验", "项目制交付经验")}],
    "I12": [{"key": "I12A", "title": "食品农产品专项", "fields": _industry_fields("食品生产许可证", "HACCP体系", "原料来源", "冷链能力", "批次追溯能力", "商超渠道经验")}],
    "I13": [{"key": "I13A", "title": "园艺农林专项", "fields": _industry_fields("园艺产品开发能力", "农机适配能力", "种苗培育能力", "病虫害防控能力", "出口检疫经验", "季节性供应保障")}],
    "I14": [{"key": "I14A", "title": "畜牧水产宠物专项", "fields": _industry_fields("饲料/用品研发能力", "养殖技术服务能力", "冷链与保鲜能力", "动物营养配方能力", "宠物品牌代工经验", "跨境电商经验")}],
    "I15": [{"key": "I15A", "title": "医疗健康专项", "fields": _industry_fields("医疗器械生产许可证", "ISO13485体系", "注册证情况", "临床验证能力", "维修校准能力", "海外法规准入经验")}],
    "I16": [{"key": "I16A", "title": "母婴个护美妆专项", "fields": _industry_fields("配方研发能力", "功效检测能力", "安全性评估", "化妆品备案经验", "品牌代工经验", "渠道运营能力")}],
    "I17": [{"key": "I17A", "title": "零售礼品专项", "fields": _industry_fields("新品开发速度", "小单快反能力", "礼品定制能力", "节庆主题策划能力", "跨境平台经验", "终端陈列支持能力")}],
    "I18": [{"key": "I18A", "title": "劳保安防专项", "fields": _industry_fields("防护标准符合性", "安防系统集成能力", "应急装备供货能力", "消防认证情况", "项目制供货经验", "培训与售后能力")}],
    "I19": [{"key": "I19A", "title": "游戏动漫专项", "fields": _industry_fields("自有IP", "授权IP", "版权证明", "用户规模", "粉丝画像", "商业化数据")}],
    "I20": [{"key": "I20A", "title": "数字科技服务专项", "fields": _industry_fields("核心技术栈", "交付团队规模", "项目管理体系", "数据安全合规能力", "SaaS/平台化能力", "行业解决方案案例")}],
}
