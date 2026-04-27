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
            {"key": "desc_scenarios", "label": "应用场景", "type": "textarea"},
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
            {"key": "other_notes", "label": "其他说明", "type": "textarea"},
        ],
    },
]


def _fields(*labels):
    return [{"key": f"f{idx}", "label": label, "type": "text"} for idx, label in enumerate(labels, start=1)]


INDUSTRY_PRODUCT_EXTRA_FIELD_CONFIG = {
    "I01": [{"key": "I01P", "title": "工业机械专项", "fields": _fields("设备型号", "设备尺寸", "设备重量", "功率", "电压", "产能", "精度", "速度", "PLC", "安装周期", "验收标准")}],
    "I02": [{"key": "I02P", "title": "电子电器专项", "fields": _fields("电压", "功率", "电流", "频率", "电池容量", "通信方式", "APP功能", "隐私政策", "跌落测试")}],
    "I03": [{"key": "I03P", "title": "电力电缆专项", "fields": _fields("额定电压", "额定电流", "绝缘等级", "耐温等级", "防护等级", "导体材质", "标准规范", "测试项目", "寿命周期")}],
    "I04": [{"key": "I04P", "title": "新能源环保专项", "fields": _fields("电池类型", "循环寿命", "转换效率", "储能容量", "环境等级", "噪音等级", "并网标准", "碳减排指标", "运维模式")}],
    "I05": [{"key": "I05P", "title": "汽车摩托专项", "fields": _fields("适配车型", "排量", "驱动形式", "燃油/电池类型", "安全标准", "耐久测试", "关键零部件", "质保里程", "售后网络")}],
    "I06": [{"key": "I06P", "title": "低空航空专项", "fields": _fields("飞行平台", "最大起飞重量", "续航时长", "最大航程", "巡航速度", "通信链路", "载荷能力", "抗风等级", "适航/认证状态")}],
    "I07": [{"key": "I07P", "title": "五金建材专项", "fields": _fields("执行标准", "防火等级", "防水等级", "抗压强度", "耐腐蚀等级", "施工方式", "安装周期", "质保年限", "项目案例")}],
    "I08": [{"key": "I08P", "title": "化工塑料专项", "fields": _fields("CAS号", "成分", "纯度", "SDS", "COA", "危险品分类", "储存条件", "运输条件")}],
    "I09": [{"key": "I09P", "title": "纺织家纺专项", "fields": _fields("纱支", "克重", "织法", "色牢度", "缩水率", "阻燃等级", "环保标准", "面辅料构成", "洗护建议")}],
    "I10": [{"key": "I10P", "title": "服装鞋帽专项", "fields": _fields("品类", "版型", "面料", "辅料", "颜色", "尺码表", "工艺", "吊牌", "水洗标")}],
    "I11": [{"key": "I11P", "title": "家居家具专项", "fields": _fields("风格", "主材", "表面工艺", "承重", "环保等级", "组装方式", "包装抗压", "空间适配", "安装说明")}],
    "I12": [{"key": "I12P", "title": "食品农饮专项", "fields": _fields("配料表", "净含量", "保质期", "储存方式", "过敏原信息", "执行标准", "产地", "营养成分", "冷链要求")}],
    "I13": [{"key": "I13P", "title": "园艺农林专项", "fields": _fields("适用作物", "作业宽度", "动力类型", "作业效率", "喷洒精度", "水肥模式", "耐候等级", "维护周期", "使用环境")}],
    "I14": [{"key": "I14P", "title": "畜牧水产宠物专项", "fields": _fields("适用对象", "蛋白/营养指标", "添加剂说明", "规格包装", "保鲜要求", "喂养/使用说明", "检测项目", "合规标准", "追溯编码")}],
    "I15": [{"key": "I15P", "title": "医疗健康专项", "fields": _fields("产品分类", "测量范围", "精度", "适用人群", "临床评价", "禁忌症", "数据存储")}],
    "I16": [{"key": "I16P", "title": "母婴个护美妆专项", "fields": _fields("适用年龄", "成分清单", "功效", "刺激性等级", "肤质/发质适配", "使用频次", "备案/注册号", "安全测试", "包装规格")}],
    "I17": [{"key": "I17P", "title": "零售礼品专项", "fields": _fields("礼品类型", "定制方式", "最小定制量", "交付周期", "节日主题", "包装方案", "品牌印刷", "渠道适配", "陈列建议")}],
    "I18": [{"key": "I18P", "title": "劳保安防专项", "fields": _fields("防护等级", "执行标准", "防割/防冲击指标", "报警方式", "联动能力", "应急响应时长", "环境适配", "培训要求", "检测周期")}],
    "I19": [{"key": "I19P", "title": "游戏动漫文创专项", "fields": _fields("IP类型", "授权范围", "版权证明", "目标用户", "运营平台", "内容分级", "商业化方式", "联名合作", "更新节奏")}],
    "I20": [{"key": "I20P", "title": "数字科技专项", "fields": _fields("功能模块", "部署方式", "API接口", "数据安全", "SLA", "价格模式")}],
}
