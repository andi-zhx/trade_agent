# 跨境经贸企业库与产品管理系统（Flask）

一个面向贸促会项目场景的轻量级管理系统，用于统一管理国内企业信息、产品信息、资质证照、外资客户需求、撮合进展和归档文件，并为后续“新企业出海方案与服务方案分析”提供数据基础。

## 一、系统目标

- 建立 **企业库**：沉淀国内企业基础信息及出海方向。
- 建立 **产品库**：管理企业产品、品类与描述信息。
- 建立 **证照库**：统一维护资质证照及有效期。
- 建立 **需求库**：记录外资客户需求与目标品类。
- 建立 **撮合台账**：跟踪撮合阶段、进展和跟进记录。
- 建立 **归档中心**：保存项目过程文件和归档资料。
- 支撑后续数据分析能力：为出海方案推荐与服务策略制定提供数据支撑。

## 二、当前功能

- Flask + SQLAlchemy 项目骨架。
- SQLite 本地数据库（默认 `trade_agent.db`）。
- 预留 PostgreSQL 升级能力（替换数据库连接字符串即可）。
- 简单登录模块（预置 `users` 表，默认账号 `admin/admin123`）。
- 中文化 Dashboard 首页，展示系统名称、统计卡片与核心模块入口。
- `python app.py` 启动时自动初始化数据库并自动建表。

## 三、项目结构

```text
trade_agent/
├── app.py
├── models.py
├── requirements.txt
├── README.md
├── trade_agent.db               # 首次启动后自动创建
├── static/
│   └── css/
│       └── style.css
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── login.html
└── uploads/                     # 预留归档文件上传目录
```

## 四、安装与运行

### 1) 创建并激活虚拟环境（推荐）

```bash
python -m venv .venv
source .venv/bin/activate    # Windows 可使用 .venv\Scripts\activate
```

### 2) 安装依赖

```bash
pip install -r requirements.txt
```

### 3) 启动系统

```bash
python app.py
```

启动后访问：

- 首页（Dashboard）：`http://127.0.0.1:5000/`
- 登录页：`http://127.0.0.1:5000/登录`

## 五、数据库模型说明

所有模型定义在 `models.py`，核心表如下：

- `enterprises`：企业主档（企业编号、企业画像、经营与产能、营收、出海需求、风险与状态）。
- `contacts`：企业联系人（法定代表人、外贸负责人、项目对接人等）。
- `products`：产品档案（产品名称、参数、价格体系、认证、包装、卖点等）。
- `qualifications`：资质证照（企业/产品层面的证书信息、有效期、状态、附件路径）。
- `foreign_clients`：外资客户（客户基础信息及联系人）。
- `demands`：外资需求（需求编号、采购要素、价格与交付条款、优先级和跟进状态）。
- `match_records`：撮合匹配记录（需求与企业/产品匹配结果、分数、推荐状态、风险提示）。
- `project_progress`：项目进展（从首联到报价、谈判、签约的阶段性跟踪）。
- `documents`：文件归档（文档类型、版本、存储路径、上传信息）。
- `audit_logs`：操作日志（操作者、动作、目标对象、明细）。
- `users`：系统登录用户（当前用于演示登录，可扩展权限体系）。

### 表关系简述

- 一个 `enterprise` 可关联多个 `contacts`、`products`、`qualifications`、`documents`。
- 一个 `foreign_client` 可关联多个 `demands`。
- 一个 `demand` 可关联多个 `match_records`。
- `project_progress` 可同时关联企业、产品、外资客户与需求。
- `documents` 可关联企业、产品与项目进展记录。

## 六、数据库初始化逻辑

### 自动初始化（推荐）

执行 `python app.py` 时会自动执行：

1. `db.create_all()` 创建所有表。
2. 检查并创建默认管理员账号 `admin/admin123`（仅首次创建）。

### 手动初始化

也可使用 Flask CLI：

```bash
flask init-db
```

> 如使用 Flask CLI，请确保环境变量 `FLASK_APP=app.py`（或等效设置）已配置。

## 七、后续建议迭代

- 增加企业、产品、资质、需求、撮合的增删改查页面。
- 增加文件上传与归档管理。
- 增加筛选检索与统计图表。
- 引入 Flask-Migrate 管理数据库版本。
- 增加角色权限（管理员、项目经理、录入员等）。
