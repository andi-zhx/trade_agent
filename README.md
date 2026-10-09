# 企业资料库

一个供小团队远程共用的企业与产品资料网站。默认流程只有三步：**新增企业 → 添加产品 → 保存**，电脑和手机浏览器都能使用。

- 企业只需填写名称；产品只需选择企业并填写名称。编号自动生成。
- 联系人、型号、价格、说明、图片及附件均可稍后补充。
- 成员共用同一批资料；管理员管理成员、备份与回收站。没有公开注册。
- 保存成功后才显示成功提示；防止重复提交，并提示过期页面的编辑冲突。
- 简洁表单不会清空原有详细字段，旧表单可从“更多资料”进入。
- 数据库与附件保存在独立目录；每天自动生成可校验的完整备份，误删资料可恢复。

## 先在本地运行

需要 Python 3.12。Windows 用户也可继续使用原有启动脚本。

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

浏览器打开 `http://127.0.0.1:5000`。仅本地开发环境提供演示账号：

- 管理员：`admin / admin123`
- 普通成员：`user / user123`

公网生产环境不会启用这些默认密码，首次启动必须配置管理员密码。备份和成员管理只对管理员开放。

## 上线网站

已提供 [Render 部署配置](render.yaml) 和 [上线、迁移、恢复指南](docs/deployment.md)。推荐先上线网站，无需先开发小程序或原生 App。

[使用此仓库部署到 Render](https://render.com/deploy?repo=https://github.com/andi-zhx/trade_agent)

需要你自己的云平台账号，并购买**有持久化磁盘的服务**。平台负责运行服务器和 HTTPS，可先用平台分配的网址，不必先买域名。费用以平台确认页为准；代码推送到 GitHub 不等于网站已上线。

## 数据保存与恢复

默认本地资料在项目目录；上线通过 `TRADE_DATA_DIR` 指向持久化磁盘。不要把数据库、附件、备份或密钥提交到 GitHub。

管理员在“备份”中生成并下载“完整资料包”，里面同时包含数据库、附件和 SHA-256 校验清单。维护命令：

```bash
python manage.py backup --output /安全位置/资料备份.zip
python manage.py restore /安全位置/资料备份.zip --to /全新目录/恢复资料
```

恢复仅写入尚不存在的新目录，校验通过后才完成，不覆盖现有资料。详细切换步骤见 [恢复指南](docs/deployment.md#从备份恢复)。

**自动备份不能保证绝对不丢数据。** 本机备份无法抵御整块磁盘损坏或云账号故障。开始存放真实业务资料前，务必将完整资料包另存到独立设备或存储，并确认云平台的磁盘快照策略。日备份最多可能丢失上次成功备份之后的修改。

## 开发与验证

```bash
python -m unittest discover -s tests -v
python -m pip check
```

测试覆盖实际录入、附件、重启保留、旧库兼容迁移、重复提交、编辑冲突、账号权限、CSRF、密码变更、自动备份与恢复。GitHub Actions 在推送和 PR 时运行测试。

生产入口是 `gunicorn -c gunicorn.conf.py wsgi:app`，固定一个进程、四个线程。SQLite 和进程内备份任务目前面向小团队；不要横向扩容或启动多个 worker。

旧详细页面的导入、导出、行业字段说明保留在 [旧版详细功能说明](docs/legacy-guide.md)。其中的界面入口和权限以当前网站为准。
