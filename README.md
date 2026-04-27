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

## 二、当前功能（第一版）

- Flask + SQLAlchemy 项目骨架。
- SQLite 本地数据库（默认 `trade_agent.db`）。
- 预留 PostgreSQL 升级能力（替换数据库连接字符串即可）。
- 简单登录模块（预置 `users` 表，默认账号 `admin/admin123`）。
- 中文化 Dashboard 首页，展示系统名称、统计卡片与核心模块入口。
- 统一布局模板（Jinja2 + Bootstrap 5）。

## 三、项目结构

```text
trade_agent/
├── app.py
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
source .venv/bin/activate    # Windows 可使用 .venv\\Scripts\\activate
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

## 五、数据库说明

### 默认数据库（SQLite）

项目默认使用：

```python
sqlite:///trade_agent.db
```

### 后续升级 PostgreSQL

在 `app.py` 中将 `SQLALCHEMY_DATABASE_URI` 改为例如：

```python
postgresql+psycopg2://user:password@localhost:5432/trade_agent
```

再执行迁移/建表流程即可完成升级。

## 六、后续建议迭代

- 增加企业、产品、资质、需求、撮合的增删改查页面。
- 增加文件上传与归档管理。
- 增加筛选检索与统计图表。
- 引入 Flask-Migrate 管理数据库版本。
- 增加角色权限（管理员、项目经理、录入员等）。
