"""产品入库表单配置（通用字段 + 行业专项字段）。"""

COMMON_PRODUCT_FIELD_GROUPS = [
    {
        "key": "A",
        "title": "A. 产品身份",
        "fields": [
            {"key": "identity_name_cn", "label": "产品中文名", "type": "text"},
            {"key": "identity_name_en", "label": "产品英文名", "type": "text"},
            {"key": "identity_model", "label": "型号", "type": "text"},
            {"key": "identity_sku", "label": "SKU", "type": "text"},
            {"key": "identity_hs_code", "label": "HS编码", "type": "text"},
            {"key": "identity_series", "label": "产品系列", "type": "text"},
        ],
    },
    {
        "key": "B",
        "title": "B. 产品说明",
        "fields": [
            {"key": "desc_usage", "label": "产品用途", "type": "textarea"},
            {"key": "positioning_scenarios", "label": "应用场景（标签）", "type": "checkbox_group", "options": ["工业生产", "家用消费", "工程项目", "医疗健康", "食品农业", "户外场景", "办公场景", "跨境电商", "其他"]},
            {"key": "desc_scenarios", "label": "应用场景", "type": "textarea"},
            {"key": "target_customer_tags", "label": "目标客户（标签）", "type": "checkbox_group", "options": ["进口商", "经销商", "批发商", "品牌商", "工程商", "商超", "电商卖家", "政府采购", "终端客户"]},
            {"key": "desc_target_customer", "label": "目标客户", "type": "textarea"},
            {"key": "desc_core_selling_points", "label": "核心卖点", "type": "textarea"},
            {"key": "desc_differentiated_advantage", "label": "差异化优势", "type": "textarea"},
        ],
    },
    {
        "key": "C",
        "title": "C. 产品参数",
        "fields": [
            {"key": "param_size", "label": "尺寸", "type": "text"},
            {"key": "param_weight", "label": "重量", "type": "text"},
            {"key": "param_material", "label": "材质", "type": "text"},
            {"key": "param_performance", "label": "性能参数", "type": "textarea"},
            {"key": "param_lifespan", "label": "使用寿命", "type": "text"},
            {"key": "param_packaging_spec", "label": "包装规格", "type": "text"},
        ],
    },
    {
        "key": "D",
        "title": "D. 价格信息",
        "fields": [
            {"key": "price_exw", "label": "出厂价", "type": "text"},
            {"key": "price_fob", "label": "FOB价", "type": "text"},
            {"key": "price_cif", "label": "CIF价", "type": "text"},
            {"key": "price_ddp", "label": "DDP参考价", "type": "text"},
            {"key": "price_tier", "label": "阶梯报价", "type": "textarea"},
            {"key": "price_validity", "label": "报价有效期", "type": "text"},
        ],
    },
    {
        "key": "E",
        "title": "E. 交易条件",
        "fields": [
            {"key": "trade_moq", "label": "MOQ", "type": "select", "options": ["10件以下", "10-100件", "100-500件", "500-1000件", "1000件以上", "按产品定制"]},
            {"key": "trade_sample_policy", "label": "样品政策", "type": "select", "options": ["免费样品", "收费样品", "可退样品费", "不支持样品", "待确认"]},
            {"key": "trade_sample_cycle", "label": "样品周期", "type": "select", "options": ["3天内", "3-7天", "7-15天", "15-30天", "30天以上"]},
            {"key": "trade_mass_cycle", "label": "批量生产周期", "type": "select", "options": ["7天内", "7-15天", "15-30天", "30-60天", "60天以上"]},
            {"key": "trade_payment_methods", "label": "付款方式", "type": "checkbox_group", "options": ["T/T", "L/C", "PayPal", "信用证", "账期", "其他"]},
            {"key": "trade_terms", "label": "贸易条款", "type": "checkbox_group", "options": ["EXW", "FOB", "CIF", "CFR", "DDP", "DAP", "FCA", "其他"]},
        ],
    },
    {
        "key": "F",
        "title": "F. 认证资料",
        "fields": [
            {"key": "cert_product", "label": "产品认证", "type": "checkbox_group", "options": ["CE", "FDA", "FCC", "RoHS", "REACH", "UL", "UKCA", "ISO", "CCC", "其他", "暂无"]},
            {"key": "cert_test_report", "label": "检测报告", "type": "select", "options": ["已提供", "未提供", "不适用"]},
            {"key": "cert_quality_report", "label": "质量报告", "type": "select", "options": ["已提供", "未提供", "不适用"]},
            {"key": "cert_market_access", "label": "目标市场准入文件", "type": "select", "options": ["已提供", "未提供", "不适用"]},
        ],
    },
    {
        "key": "G",
        "title": "G. 物流信息",
        "fields": [
            {"key": "log_port", "label": "起运港", "type": "text"},
            {"key": "log_container_load", "label": "装箱量", "type": "text"},
            {"key": "log_package_type", "label": "包装方式", "type": "checkbox_group", "options": ["纸箱", "木箱", "托盘", "彩盒", "袋装", "桶装", "吨包", "其他"]},
            {"key": "log_transport_methods", "label": "运输方式", "type": "checkbox_group", "options": ["海运", "空运", "铁路", "陆运", "快递", "多式联运"]},
        ],
    },
    {
        "key": "H",
        "title": "H. 售后服务",
        "fields": [
            {"key": "after_warranty", "label": "质保期", "type": "select", "options": ["无", "3个月", "6个月", "1年", "2年", "3年以上"]},
            {"key": "after_return_policy", "label": "退换货政策", "type": "select", "options": ["支持", "不支持", "视情况协商", "待确认"]},
            {"key": "after_spare_parts", "label": "备件供应", "type": "select", "options": ["支持", "不支持", "不适用", "待确认"]},
            {"key": "after_oversea_support", "label": "海外售后支持", "type": "select", "options": ["有", "无", "通过代理商", "远程支持", "待确认"]},
            {"key": "support_customization", "label": "是否支持定制", "type": "select", "options": ["是", "否", "视情况", "待确认"]},
            {"key": "fit_cross_border", "label": "是否适合跨境电商", "type": "select", "options": ["是", "否", "待判断"]},
            {"key": "fit_engineering", "label": "是否适合工程采购", "type": "select", "options": ["是", "否", "待判断"]},
            {"key": "fit_distributor", "label": "是否适合经销代理", "type": "select", "options": ["是", "否", "待判断"]},
            {"key": "target_market_tags", "label": "目标市场（标签）", "type": "checkbox_group", "options": ["东南亚", "欧洲", "北美", "南美", "中东", "非洲", "日本韩国", "澳新", "其他"]},
            {"key": "cooperation_modes", "label": "合作模式", "type": "checkbox_group", "options": ["采购撮合", "经销代理", "OEM", "ODM", "联合开发", "工程项目", "跨境电商", "展会推荐"]},
            {"key": "product_status_review", "label": "产品状态（业务）", "type": "select", "options": ["草稿", "待补充", "已入库", "已推荐", "暂停", "下架"]},
        ],
    },
    {
        "key": "I",
        "title": "I. 展示资料",
        "fields": [
            {"key": "media_product_images", "label": "产品图片", "type": "select", "options": ["已提供", "未提供", "待补充"]},
            {"key": "media_product_videos", "label": "产品视频", "type": "select", "options": ["已提供", "未提供", "待补充"]},
            {"key": "media_manual", "label": "说明书", "type": "select", "options": ["已提供", "未提供", "待补充"]},
            {"key": "media_brochure", "label": "宣传册", "type": "select", "options": ["已提供", "未提供", "待补充"]},
            {"key": "media_english_ppt", "label": "英文PPT", "type": "select", "options": ["已提供", "未提供", "待补充"]},
            {"key": "media_case_study", "label": "案例资料", "type": "select", "options": ["已提供", "未提供", "待补充"]},
            {"key": "risk_warning", "label": "风险提示", "type": "textarea"},
            {"key": "other_notes", "label": "其他说明", "type": "textarea"},
        ],
    },
]


from config.industry_config import INDUSTRY_PRODUCT_EXTRA_FIELD_CONFIG
