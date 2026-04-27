"""行业配置中心：统一维护行业分类、覆盖范围、行业专项字段及审核要点。"""


INDUSTRY_CONFIG = {
    "I01": {
        "code": "I01",
        "name": "工业机械与装备",
        "scope": "工业母机、加工中心、自动化产线、通用机械与专用装备",
        "enterprise": {
            "key": "I01A",
            "title": "工业机械专项",
            "fields": [
                {"key": "f1", "label": "设备加工能力", "type": "text"},
                {"key": "f2", "label": "装配能力", "type": "text"},
                {"key": "f3", "label": "调试能力", "type": "text"},
                {"key": "f4", "label": "研发团队人数", "type": "text"},
                {"key": "f5", "label": "已交付设备案例", "type": "textarea"},
                {"key": "f6", "label": "海外项目经验", "type": "textarea"},
                {"key": "f7", "label": "售后备件能力", "type": "text"},
            ],
        },
        "product": {
            "key": "I01P",
            "title": "工业机械专项",
            "fields": [
                {"key": "f1", "label": "设备型号", "type": "text"},
                {"key": "f2", "label": "设备尺寸", "type": "text"},
                {"key": "f3", "label": "设备重量", "type": "text"},
                {"key": "f4", "label": "功率", "type": "text"},
                {"key": "f5", "label": "电压", "type": "text"},
                {"key": "f6", "label": "产能", "type": "text"},
                {"key": "f7", "label": "精度", "type": "text"},
                {"key": "f8", "label": "速度", "type": "text"},
                {"key": "f9", "label": "PLC", "type": "text"},
                {"key": "f10", "label": "安装周期", "type": "text"},
                {"key": "f11", "label": "验收标准", "type": "text"},
            ],
        },
        "focus_qualifications": ["ISO 9001", "CE（如出口欧盟）", "特种设备相关许可（如适用）"],
        "focus_questions": ["是否具备整线交付能力？", "关键零部件是否可追溯？", "海外安装/售后如何保障？"],
    },
    "I02": {
        "code": "I02",
        "name": "电子电器与智能硬件",
        "scope": "消费电子、家电、传感器、智能终端、物联网硬件",
        "enterprise": {
            "key": "I02A",
            "title": "电子电器专项",
            "fields": [
                {"key": "f1", "label": "硬件研发能力", "type": "text"},
                {"key": "f2", "label": "软件研发能力", "type": "text"},
                {"key": "f3", "label": "SMT产线", "type": "text"},
                {"key": "f4", "label": "老化测试线", "type": "text"},
                {"key": "f5", "label": "芯片供应链", "type": "text"},
                {"key": "f6", "label": "品牌代工经验", "type": "textarea"},
            ],
        },
        "product": {
            "key": "I02P",
            "title": "电子电器专项",
            "fields": [
                {"key": "f1", "label": "电压", "type": "text"},
                {"key": "f2", "label": "功率", "type": "text"},
                {"key": "f3", "label": "电流", "type": "text"},
                {"key": "f4", "label": "频率", "type": "text"},
                {"key": "f5", "label": "电池容量", "type": "text"},
                {"key": "f6", "label": "通信方式", "type": "text"},
                {"key": "f7", "label": "APP功能", "type": "text"},
                {"key": "f8", "label": "隐私政策", "type": "text"},
                {"key": "f9", "label": "跌落测试", "type": "text"},
            ],
        },
        "focus_qualifications": ["CE/FCC/RoHS", "UL（如适用）", "ISO 9001"],
        "focus_questions": ["核心器件是否受限于单一供应商？", "是否有EMC/安规测试报告？", "软硬件版本如何管理？"],
    },
    "I03": {
        "code": "I03",
        "name": "电力、电缆与能源设备",
        "scope": "输配电设备、电线电缆、电力控制设备与能源配套装备",
        "enterprise": {"key": "I03A", "title": "电力能源专项", "fields": [{"key": "f1", "label": "高低压设备能力", "type": "text"}, {"key": "f2", "label": "电缆制造能力", "type": "text"}, {"key": "f3", "label": "变配电成套经验", "type": "textarea"}, {"key": "f4", "label": "并网项目经验", "type": "textarea"}, {"key": "f5", "label": "关键认证资质", "type": "text"}, {"key": "f6", "label": "海外电力标准适配", "type": "text"}]},
        "product": {"key": "I03P", "title": "电力电缆专项", "fields": [{"key": "f1", "label": "额定电压", "type": "text"}, {"key": "f2", "label": "额定电流", "type": "text"}, {"key": "f3", "label": "绝缘等级", "type": "text"}, {"key": "f4", "label": "耐温等级", "type": "text"}, {"key": "f5", "label": "防护等级", "type": "text"}, {"key": "f6", "label": "导体材质", "type": "text"}, {"key": "f7", "label": "标准规范", "type": "text"}, {"key": "f8", "label": "测试项目", "type": "text"}, {"key": "f9", "label": "寿命周期", "type": "text"}]},
        "focus_qualifications": ["型式试验报告", "ISO 9001", "电工产品认证（CCC/CE等）"],
        "focus_questions": ["执行标准是否覆盖目标市场？", "耐压与温升测试是否齐全？", "是否有大型项目交付案例？"],
    },
    "I04": {
        "code": "I04", "name": "新能源与节能环保", "scope": "光伏、储能、节能设备、环保处理设备与绿色技术",
        "enterprise": {"key": "I04A", "title": "新能源环保专项", "fields": [{"key": "f1", "label": "光储系统集成能力", "type": "text"}, {"key": "f2", "label": "节能解决方案能力", "type": "text"}, {"key": "f3", "label": "环保处理工艺", "type": "text"}, {"key": "f4", "label": "碳排管理能力", "type": "text"}, {"key": "f5", "label": "新能源项目案例", "type": "textarea"}, {"key": "f6", "label": "海外运维服务能力", "type": "text"}]},
        "product": {"key": "I04P", "title": "新能源环保专项", "fields": [{"key": "f1", "label": "电池类型", "type": "text"}, {"key": "f2", "label": "循环寿命", "type": "text"}, {"key": "f3", "label": "转换效率", "type": "text"}, {"key": "f4", "label": "储能容量", "type": "text"}, {"key": "f5", "label": "环境等级", "type": "text"}, {"key": "f6", "label": "噪音等级", "type": "text"}, {"key": "f7", "label": "并网标准", "type": "text"}, {"key": "f8", "label": "碳减排指标", "type": "text"}, {"key": "f9", "label": "运维模式", "type": "text"}]},
        "focus_qualifications": ["IEC相关认证", "并网合规文件", "ISO 14001"],
        "focus_questions": ["系统效率和衰减数据是否可验证？", "关键部件寿命是否有报告？", "是否具备本地化运维能力？"],
    },
    "I05": {"code": "I05", "name": "汽车、摩托车与零部件", "scope": "整车、摩托车、汽车电子、动力系统与零配件", "enterprise": {"key": "I05A", "title": "汽车摩托专项", "fields": [{"key": "f1", "label": "整车/零部件开发能力", "type": "text"}, {"key": "f2", "label": "IATF16949体系", "type": "text"}, {"key": "f3", "label": "关键零部件测试能力", "type": "text"}, {"key": "f4", "label": "主机厂配套经验", "type": "textarea"}, {"key": "f5", "label": "售后备件供应能力", "type": "text"}, {"key": "f6", "label": "海外认证经验", "type": "textarea"}]}, "product": {"key": "I05P", "title": "汽车摩托专项", "fields": [{"key": "f1", "label": "适配车型", "type": "text"}, {"key": "f2", "label": "排量", "type": "text"}, {"key": "f3", "label": "驱动形式", "type": "text"}, {"key": "f4", "label": "燃油/电池类型", "type": "text"}, {"key": "f5", "label": "安全标准", "type": "text"}, {"key": "f6", "label": "耐久测试", "type": "text"}, {"key": "f7", "label": "关键零部件", "type": "text"}, {"key": "f8", "label": "质保里程", "type": "text"}, {"key": "f9", "label": "售后网络", "type": "text"}]}, "focus_qualifications": ["IATF 16949", "ECE/DOT等目标市场认证", "PPAP/APQP资料"], "focus_questions": ["是否通过主机厂体系审核？", "失效分析和召回机制是否完善？", "关键安全件验证是否齐全？"]},
    "I06": {"code": "I06", "name": "低空经济与航空装备", "scope": "无人机、通航设备、低空基础设施与航空配套装备", "enterprise": {"key": "I06A", "title": "低空经济专项", "fields": [{"key": "f1", "label": "飞控系统能力", "type": "text"}, {"key": "f2", "label": "机体结构设计能力", "type": "text"}, {"key": "f3", "label": "任务载荷集成能力", "type": "text"}, {"key": "f4", "label": "试飞测试能力", "type": "text"}, {"key": "f5", "label": "适航/合规准备情况", "type": "text"}, {"key": "f6", "label": "海外项目经验", "type": "textarea"}]}, "product": {"key": "I06P", "title": "低空航空专项", "fields": [{"key": "f1", "label": "飞行平台", "type": "text"}, {"key": "f2", "label": "最大起飞重量", "type": "text"}, {"key": "f3", "label": "续航时长", "type": "text"}, {"key": "f4", "label": "最大航程", "type": "text"}, {"key": "f5", "label": "巡航速度", "type": "text"}, {"key": "f6", "label": "通信链路", "type": "text"}, {"key": "f7", "label": "载荷能力", "type": "text"}, {"key": "f8", "label": "抗风等级", "type": "text"}, {"key": "f9", "label": "适航/认证状态", "type": "text"}]}, "focus_qualifications": ["适航符合性材料", "无线电型号核准（如适用）", "出口管制合规文件"], "focus_questions": ["飞行安全冗余设计是否说明清晰？", "是否可提供飞测数据和日志？", "目标国家空域合规如何满足？"]},
    "I07": {"code": "I07", "name": "五金、建材与建筑工程", "scope": "五金工具、建筑材料、工程设备与施工配套", "enterprise": {"key": "I07A", "title": "五金建材专项", "fields": [{"key": "f1", "label": "材料加工能力", "type": "text"}, {"key": "f2", "label": "工程配套能力", "type": "text"}, {"key": "f3", "label": "防火/防水标准能力", "type": "text"}, {"key": "f4", "label": "施工交付经验", "type": "textarea"}, {"key": "f5", "label": "大型项目案例", "type": "textarea"}, {"key": "f6", "label": "现场服务能力", "type": "text"}]}, "product": {"key": "I07P", "title": "五金建材专项", "fields": [{"key": "f1", "label": "执行标准", "type": "text"}, {"key": "f2", "label": "防火等级", "type": "text"}, {"key": "f3", "label": "防水等级", "type": "text"}, {"key": "f4", "label": "抗压强度", "type": "text"}, {"key": "f5", "label": "耐腐蚀等级", "type": "text"}, {"key": "f6", "label": "施工方式", "type": "text"}, {"key": "f7", "label": "安装周期", "type": "text"}, {"key": "f8", "label": "质保年限", "type": "text"}, {"key": "f9", "label": "项目案例", "type": "text"}]}, "focus_qualifications": ["建材检测报告", "防火/防水等级文件", "ISO 9001"], "focus_questions": ["执行标准是否与采购地一致？", "耐久性测试周期是否足够？", "安装和售后责任如何划分？"]},
    "I08": {"code": "I08", "name": "化工、塑料与新材料", "scope": "基础化工、精细化工、塑料制品、复合材料与新材料", "enterprise": {"key": "I08A", "title": "化工新材料专项", "fields": [{"key": "f1", "label": "核心配方能力", "type": "text"}, {"key": "f2", "label": "中试放大能力", "type": "text"}, {"key": "f3", "label": "危险品合规能力", "type": "text"}, {"key": "f4", "label": "MSDS与REACH准备", "type": "text"}, {"key": "f5", "label": "稳定供货能力", "type": "text"}, {"key": "f6", "label": "海外法规符合性", "type": "text"}]}, "product": {"key": "I08P", "title": "化工塑料专项", "fields": [{"key": "f1", "label": "CAS号", "type": "text"}, {"key": "f2", "label": "成分", "type": "text"}, {"key": "f3", "label": "纯度", "type": "text"}, {"key": "f4", "label": "SDS", "type": "text"}, {"key": "f5", "label": "COA", "type": "text"}, {"key": "f6", "label": "危险品分类", "type": "text"}, {"key": "f7", "label": "储存条件", "type": "text"}, {"key": "f8", "label": "运输条件", "type": "text"}]}, "focus_qualifications": ["SDS/MSDS", "REACH/RoHS（如适用）", "危险化学品经营/生产许可（如适用）"], "focus_questions": ["成分与杂质控制范围是否明确？", "批次一致性和COA是否可追溯？", "危化运输和仓储是否合规？"]},
    "I09": {"code": "I09", "name": "纺织、面辅料与家纺", "scope": "纱线面料、辅料、家用纺织品与纺织供应链", "enterprise": {"key": "I09A", "title": "纺织家纺专项", "fields": [{"key": "f1", "label": "织造染整能力", "type": "text"}, {"key": "f2", "label": "面辅料开发能力", "type": "text"}, {"key": "f3", "label": "打样反应速度", "type": "text"}, {"key": "f4", "label": "质量检验体系", "type": "text"}, {"key": "f5", "label": "快返单能力", "type": "text"}, {"key": "f6", "label": "国际品牌供货经验", "type": "textarea"}]}, "product": {"key": "I09P", "title": "纺织家纺专项", "fields": [{"key": "f1", "label": "纱支", "type": "text"}, {"key": "f2", "label": "克重", "type": "text"}, {"key": "f3", "label": "织法", "type": "text"}, {"key": "f4", "label": "色牢度", "type": "text"}, {"key": "f5", "label": "缩水率", "type": "text"}, {"key": "f6", "label": "阻燃等级", "type": "text"}, {"key": "f7", "label": "环保标准", "type": "text"}, {"key": "f8", "label": "面辅料构成", "type": "text"}, {"key": "f9", "label": "洗护建议", "type": "text"}]}, "focus_qualifications": ["OEKO-TEX/GRS（如适用）", "色牢度/甲醛检测", "BSCI/SEDEX（如适用）"], "focus_questions": ["面料批次色差如何控制？", "是否支持小单快反？", "环保与可持续认证是否有效？"]},
    "I10": {"code": "I10", "name": "服装服饰与鞋帽箱包", "scope": "服装成衣、配饰、鞋履、帽类、箱包与时尚用品", "enterprise": {"key": "I10A", "title": "服饰鞋帽专项", "fields": [{"key": "f1", "label": "版型开发能力", "type": "text"}, {"key": "f2", "label": "柔性生产能力", "type": "text"}, {"key": "f3", "label": "鞋包打样能力", "type": "text"}, {"key": "f4", "label": "时尚趋势响应能力", "type": "text"}, {"key": "f5", "label": "品牌合作经验", "type": "textarea"}, {"key": "f6", "label": "可持续材料应用", "type": "text"}]}, "product": {"key": "I10P", "title": "服装鞋帽专项", "fields": [{"key": "f1", "label": "品类", "type": "text"}, {"key": "f2", "label": "版型", "type": "text"}, {"key": "f3", "label": "面料", "type": "text"}, {"key": "f4", "label": "辅料", "type": "text"}, {"key": "f5", "label": "颜色", "type": "text"}, {"key": "f6", "label": "尺码表", "type": "text"}, {"key": "f7", "label": "工艺", "type": "text"}, {"key": "f8", "label": "吊牌", "type": "text"}, {"key": "f9", "label": "水洗标", "type": "text"}]}, "focus_qualifications": ["成分检测报告", "REACH/加州65（如适用）", "社会责任审核"], "focus_questions": ["尺码标准是否匹配目标市场？", "可否提供打样与翻单时效？", "辅料合规文件是否完备？"]},
    "I11": {"code": "I11", "name": "家居、家具与生活用品", "scope": "家具、家居用品、厨卫用品、日用消费品", "enterprise": {"key": "I11A", "title": "家居家具专项", "fields": [{"key": "f1", "label": "家具结构设计能力", "type": "text"}, {"key": "f2", "label": "板木金工艺能力", "type": "text"}, {"key": "f3", "label": "整装配套能力", "type": "text"}, {"key": "f4", "label": "包装抗损能力", "type": "text"}, {"key": "f5", "label": "海外仓配经验", "type": "textarea"}, {"key": "f6", "label": "项目制交付经验", "type": "textarea"}]}, "product": {"key": "I11P", "title": "家居家具专项", "fields": [{"key": "f1", "label": "风格", "type": "text"}, {"key": "f2", "label": "主材", "type": "text"}, {"key": "f3", "label": "表面工艺", "type": "text"}, {"key": "f4", "label": "承重", "type": "text"}, {"key": "f5", "label": "环保等级", "type": "text"}, {"key": "f6", "label": "组装方式", "type": "text"}, {"key": "f7", "label": "包装抗压", "type": "text"}, {"key": "f8", "label": "空间适配", "type": "text"}, {"key": "f9", "label": "安装说明", "type": "text"}]}, "focus_qualifications": ["甲醛/VOC检测", "BIFMA/EN家具标准（如适用）", "包装跌落测试报告"], "focus_questions": ["平板包装与安装复杂度如何？", "材质环保等级是否可证明？", "大件物流破损率如何控制？"]},
    "I12": {"code": "I12", "name": "食品、农产品与饮料", "scope": "预包装食品、农副产品、休闲食品与各类饮品", "enterprise": {"key": "I12A", "title": "食品农产品专项", "fields": [{"key": "f1", "label": "食品生产许可证", "type": "text"}, {"key": "f2", "label": "HACCP体系", "type": "text"}, {"key": "f3", "label": "原料来源", "type": "text"}, {"key": "f4", "label": "冷链能力", "type": "text"}, {"key": "f5", "label": "批次追溯能力", "type": "text"}, {"key": "f6", "label": "商超渠道经验", "type": "textarea"}]}, "product": {"key": "I12P", "title": "食品农饮专项", "fields": [{"key": "f1", "label": "配料表", "type": "text"}, {"key": "f2", "label": "净含量", "type": "text"}, {"key": "f3", "label": "保质期", "type": "text"}, {"key": "f4", "label": "储存方式", "type": "text"}, {"key": "f5", "label": "过敏原信息", "type": "text"}, {"key": "f6", "label": "执行标准", "type": "text"}, {"key": "f7", "label": "产地", "type": "text"}, {"key": "f8", "label": "营养成分", "type": "text"}, {"key": "f9", "label": "冷链要求", "type": "text"}]}, "focus_qualifications": ["SC生产许可", "HACCP/ISO22000", "第三方检测报告"], "focus_questions": ["原料批次和供应地是否可追溯？", "标签合规是否符合目标市场？", "冷链温控记录是否可提供？"]},
    "I13": {"code": "I13", "name": "园艺、花卉与农林设备", "scope": "园艺用品、花卉苗木、农业机械与林业装备", "enterprise": {"key": "I13A", "title": "园艺农林专项", "fields": [{"key": "f1", "label": "园艺产品开发能力", "type": "text"}, {"key": "f2", "label": "农机适配能力", "type": "text"}, {"key": "f3", "label": "种苗培育能力", "type": "text"}, {"key": "f4", "label": "病虫害防控能力", "type": "text"}, {"key": "f5", "label": "出口检疫经验", "type": "textarea"}, {"key": "f6", "label": "季节性供应保障", "type": "text"}]}, "product": {"key": "I13P", "title": "园艺农林专项", "fields": [{"key": "f1", "label": "适用作物", "type": "text"}, {"key": "f2", "label": "作业宽度", "type": "text"}, {"key": "f3", "label": "动力类型", "type": "text"}, {"key": "f4", "label": "作业效率", "type": "text"}, {"key": "f5", "label": "喷洒精度", "type": "text"}, {"key": "f6", "label": "水肥模式", "type": "text"}, {"key": "f7", "label": "耐候等级", "type": "text"}, {"key": "f8", "label": "维护周期", "type": "text"}, {"key": "f9", "label": "使用环境", "type": "text"}]}, "focus_qualifications": ["农机相关检测报告", "植检/检疫文件（如适用）", "农资登记（如适用）"], "focus_questions": ["季节性产能波动如何管理？", "是否适配目标地区作物条件？", "售后维保覆盖范围如何？"]},
    "I14": {"code": "I14", "name": "畜牧、水产与宠物产业", "scope": "畜牧养殖、水产养殖、宠物食品、宠物用品与设备", "enterprise": {"key": "I14A", "title": "畜牧水产宠物专项", "fields": [{"key": "f1", "label": "饲料/用品研发能力", "type": "text"}, {"key": "f2", "label": "养殖技术服务能力", "type": "text"}, {"key": "f3", "label": "冷链与保鲜能力", "type": "text"}, {"key": "f4", "label": "动物营养配方能力", "type": "text"}, {"key": "f5", "label": "宠物品牌代工经验", "type": "textarea"}, {"key": "f6", "label": "跨境电商经验", "type": "textarea"}]}, "product": {"key": "I14P", "title": "畜牧水产宠物专项", "fields": [{"key": "f1", "label": "适用对象", "type": "text"}, {"key": "f2", "label": "蛋白/营养指标", "type": "text"}, {"key": "f3", "label": "添加剂说明", "type": "text"}, {"key": "f4", "label": "规格包装", "type": "text"}, {"key": "f5", "label": "保鲜要求", "type": "text"}, {"key": "f6", "label": "喂养/使用说明", "type": "text"}, {"key": "f7", "label": "检测项目", "type": "text"}, {"key": "f8", "label": "合规标准", "type": "text"}, {"key": "f9", "label": "追溯编码", "type": "text"}]}, "focus_qualifications": ["饲料/宠物食品生产许可", "检验检疫文件", "营养/微生物检测报告"], "focus_questions": ["是否具备批次追溯和召回机制？", "添加剂是否满足进口国要求？", "冷链运输方案是否稳定？"]},
    "I15": {"code": "I15", "name": "医疗器械与健康产品", "scope": "医疗设备、康复器材、健康监测与医用耗材", "enterprise": {"key": "I15A", "title": "医疗健康专项", "fields": [{"key": "f1", "label": "医疗器械生产许可证", "type": "text"}, {"key": "f2", "label": "ISO13485体系", "type": "text"}, {"key": "f3", "label": "注册证情况", "type": "text"}, {"key": "f4", "label": "临床验证能力", "type": "text"}, {"key": "f5", "label": "维修校准能力", "type": "text"}, {"key": "f6", "label": "海外法规准入经验", "type": "textarea"}]}, "product": {"key": "I15P", "title": "医疗健康专项", "fields": [{"key": "f1", "label": "产品分类", "type": "text"}, {"key": "f2", "label": "测量范围", "type": "text"}, {"key": "f3", "label": "精度", "type": "text"}, {"key": "f4", "label": "适用人群", "type": "text"}, {"key": "f5", "label": "临床评价", "type": "text"}, {"key": "f6", "label": "禁忌症", "type": "text"}, {"key": "f7", "label": "数据存储", "type": "text"}]}, "focus_qualifications": ["医疗器械注册/备案", "ISO 13485", "CE MDR/FDA（如适用）"], "focus_questions": ["产品风险等级与注册路径是否匹配？", "临床证据是否充分？", "售后维修与校准体系是否完善？"]},
    "I16": {"code": "I16", "name": "母婴、个护与美妆", "scope": "母婴用品、个护产品、美妆护肤与相关配套", "enterprise": {"key": "I16A", "title": "母婴个护美妆专项", "fields": [{"key": "f1", "label": "配方研发能力", "type": "text"}, {"key": "f2", "label": "功效检测能力", "type": "text"}, {"key": "f3", "label": "安全性评估", "type": "text"}, {"key": "f4", "label": "化妆品备案经验", "type": "text"}, {"key": "f5", "label": "品牌代工经验", "type": "textarea"}, {"key": "f6", "label": "渠道运营能力", "type": "text"}]}, "product": {"key": "I16P", "title": "母婴个护美妆专项", "fields": [{"key": "f1", "label": "适用年龄", "type": "text"}, {"key": "f2", "label": "成分清单", "type": "text"}, {"key": "f3", "label": "功效", "type": "text"}, {"key": "f4", "label": "刺激性等级", "type": "text"}, {"key": "f5", "label": "肤质/发质适配", "type": "text"}, {"key": "f6", "label": "使用频次", "type": "text"}, {"key": "f7", "label": "备案/注册号", "type": "text"}, {"key": "f8", "label": "安全测试", "type": "text"}, {"key": "f9", "label": "包装规格", "type": "text"}]}, "focus_qualifications": ["化妆品备案/注册", "微生物与重金属检测", "GMPC/ISO 22716（如适用）"], "focus_questions": ["配方合规是否覆盖目标市场禁限用物质？", "功效宣称是否有证据支持？", "婴童产品安全测试是否充分？"]},
    "I17": {"code": "I17", "name": "零售消费品与礼品", "scope": "百货零售商品、促销礼品、节庆礼品与定制礼赠", "enterprise": {"key": "I17A", "title": "零售礼品专项", "fields": [{"key": "f1", "label": "新品开发速度", "type": "text"}, {"key": "f2", "label": "小单快反能力", "type": "text"}, {"key": "f3", "label": "礼品定制能力", "type": "text"}, {"key": "f4", "label": "节庆主题策划能力", "type": "text"}, {"key": "f5", "label": "跨境平台经验", "type": "textarea"}, {"key": "f6", "label": "终端陈列支持能力", "type": "text"}]}, "product": {"key": "I17P", "title": "零售礼品专项", "fields": [{"key": "f1", "label": "礼品类型", "type": "text"}, {"key": "f2", "label": "定制方式", "type": "text"}, {"key": "f3", "label": "最小定制量", "type": "text"}, {"key": "f4", "label": "交付周期", "type": "text"}, {"key": "f5", "label": "节日主题", "type": "text"}, {"key": "f6", "label": "包装方案", "type": "text"}, {"key": "f7", "label": "品牌印刷", "type": "text"}, {"key": "f8", "label": "渠道适配", "type": "text"}, {"key": "f9", "label": "陈列建议", "type": "text"}]}, "focus_qualifications": ["材料安全检测报告", "知识产权授权文件（如适用）", "质量管理体系文件"], "focus_questions": ["定制打样与交付周期是否可控？", "节庆峰值订单如何保供？", "品牌授权与侵权风险如何规避？"]},
    "I18": {"code": "I18", "name": "劳保、安防与应急装备", "scope": "劳保用品、安防设备、消防器材与应急救援装备", "enterprise": {"key": "I18A", "title": "劳保安防专项", "fields": [{"key": "f1", "label": "防护标准符合性", "type": "text"}, {"key": "f2", "label": "安防系统集成能力", "type": "text"}, {"key": "f3", "label": "应急装备供货能力", "type": "text"}, {"key": "f4", "label": "消防认证情况", "type": "text"}, {"key": "f5", "label": "项目制供货经验", "type": "textarea"}, {"key": "f6", "label": "培训与售后能力", "type": "text"}]}, "product": {"key": "I18P", "title": "劳保安防专项", "fields": [{"key": "f1", "label": "防护等级", "type": "text"}, {"key": "f2", "label": "执行标准", "type": "text"}, {"key": "f3", "label": "防割/防冲击指标", "type": "text"}, {"key": "f4", "label": "报警方式", "type": "text"}, {"key": "f5", "label": "联动能力", "type": "text"}, {"key": "f6", "label": "应急响应时长", "type": "text"}, {"key": "f7", "label": "环境适配", "type": "text"}, {"key": "f8", "label": "培训要求", "type": "text"}, {"key": "f9", "label": "检测周期", "type": "text"}]}, "focus_qualifications": ["EN/ANSI/GB防护标准认证", "消防产品认证（如适用）", "第三方性能测试报告"], "focus_questions": ["关键防护指标是否有权威报告？", "系统联动兼容性如何验证？", "应急场景交付时效能否保证？"]},
    "I19": {"code": "I19", "name": "游戏、动漫与文化创意", "scope": "游戏内容、动漫衍生品、IP文创与数字文娱产品", "enterprise": {"key": "I19A", "title": "游戏动漫专项", "fields": [{"key": "f1", "label": "自有IP", "type": "text"}, {"key": "f2", "label": "授权IP", "type": "text"}, {"key": "f3", "label": "版权证明", "type": "text"}, {"key": "f4", "label": "用户规模", "type": "text"}, {"key": "f5", "label": "粉丝画像", "type": "text"}, {"key": "f6", "label": "商业化数据", "type": "text"}]}, "product": {"key": "I19P", "title": "游戏动漫文创专项", "fields": [{"key": "f1", "label": "IP类型", "type": "text"}, {"key": "f2", "label": "授权范围", "type": "text"}, {"key": "f3", "label": "版权证明", "type": "text"}, {"key": "f4", "label": "目标用户", "type": "text"}, {"key": "f5", "label": "运营平台", "type": "text"}, {"key": "f6", "label": "内容分级", "type": "text"}, {"key": "f7", "label": "商业化方式", "type": "text"}, {"key": "f8", "label": "联名合作", "type": "text"}, {"key": "f9", "label": "更新节奏", "type": "text"}]}, "focus_qualifications": ["版权/商标权属证明", "授权链路文件", "内容合规审查材料"], "focus_questions": ["IP权属是否完整且可转授权？", "不同市场内容分级是否合规？", "商业化数据是否可核验？"]},
    "I20": {"code": "I20", "name": "数字科技与专业服务", "scope": "软件服务、数字化解决方案、咨询服务与专业技术服务", "enterprise": {"key": "I20A", "title": "数字科技服务专项", "fields": [{"key": "f1", "label": "核心技术栈", "type": "text"}, {"key": "f2", "label": "交付团队规模", "type": "text"}, {"key": "f3", "label": "项目管理体系", "type": "text"}, {"key": "f4", "label": "数据安全合规能力", "type": "text"}, {"key": "f5", "label": "SaaS/平台化能力", "type": "text"}, {"key": "f6", "label": "行业解决方案案例", "type": "textarea"}]}, "product": {"key": "I20P", "title": "数字科技专项", "fields": [{"key": "f1", "label": "功能模块", "type": "text"}, {"key": "f2", "label": "部署方式", "type": "text"}, {"key": "f3", "label": "API接口", "type": "text"}, {"key": "f4", "label": "数据安全", "type": "text"}, {"key": "f5", "label": "SLA", "type": "text"}, {"key": "f6", "label": "价格模式", "type": "text"}]}, "focus_qualifications": ["ISO 27001", "等保/隐私合规文件", "服务SLA模板"], "focus_questions": ["数据主权与跨境传输如何处理？", "系统可用性与恢复目标如何承诺？", "交付与运维边界是否清晰？"]},
}

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
