from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "replace-with-a-secure-secret-key"
# 当前默认 SQLite，后续可直接替换为 PostgreSQL 连接串，例如：
# postgresql+psycopg2://user:password@localhost:5432/trade_agent
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'trade_agent.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    """预留用户表，后续可扩展权限体系。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    用户名 = db.Column(db.String(50), unique=True, nullable=False)
    密码 = db.Column(db.String(128), nullable=False)
    角色 = db.Column(db.String(50), default="管理员")
    创建时间 = db.Column(db.DateTime, default=datetime.utcnow)


class Enterprise(db.Model):
    """企业基础信息。"""

    __tablename__ = "enterprises"

    id = db.Column(db.Integer, primary_key=True)
    企业名称 = db.Column(db.String(200), nullable=False)
    所属地区 = db.Column(db.String(100))
    行业类别 = db.Column(db.String(100))
    联系人 = db.Column(db.String(100))
    联系电话 = db.Column(db.String(50))
    出海目标市场 = db.Column(db.String(200))
    创建时间 = db.Column(db.DateTime, default=datetime.utcnow)


class Product(db.Model):
    """企业产品信息。"""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    产品名称 = db.Column(db.String(200), nullable=False)
    产品类别 = db.Column(db.String(100))
    产品描述 = db.Column(db.Text)
    企业id = db.Column(db.Integer, db.ForeignKey("enterprises.id"), nullable=True)
    创建时间 = db.Column(db.DateTime, default=datetime.utcnow)


class Qualification(db.Model):
    """资质证照信息。"""

    __tablename__ = "qualifications"

    id = db.Column(db.Integer, primary_key=True)
    证照名称 = db.Column(db.String(200), nullable=False)
    证照编号 = db.Column(db.String(100))
    有效期至 = db.Column(db.Date)
    企业id = db.Column(db.Integer, db.ForeignKey("enterprises.id"), nullable=True)


class ClientNeed(db.Model):
    """外资客户需求。"""

    __tablename__ = "client_needs"

    id = db.Column(db.Integer, primary_key=True)
    客户名称 = db.Column(db.String(200), nullable=False)
    国家地区 = db.Column(db.String(100))
    需求描述 = db.Column(db.Text)
    目标产品类别 = db.Column(db.String(100))
    紧急程度 = db.Column(db.String(50), default="中")
    创建时间 = db.Column(db.DateTime, default=datetime.utcnow)


class MatchProgress(db.Model):
    """撮合进展记录。"""

    __tablename__ = "match_progress"

    id = db.Column(db.Integer, primary_key=True)
    企业id = db.Column(db.Integer, db.ForeignKey("enterprises.id"), nullable=True)
    客户需求id = db.Column(db.Integer, db.ForeignKey("client_needs.id"), nullable=True)
    进展状态 = db.Column(db.String(100), default="待启动")
    跟进记录 = db.Column(db.Text)
    更新时间 = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ArchiveFile(db.Model):
    """归档文件元数据。"""

    __tablename__ = "archive_files"

    id = db.Column(db.Integer, primary_key=True)
    文件名称 = db.Column(db.String(255), nullable=False)
    文件路径 = db.Column(db.String(500), nullable=False)
    关联模块 = db.Column(db.String(100))
    上传时间 = db.Column(db.DateTime, default=datetime.utcnow)


@app.route("/")
def dashboard():
    企业数量 = Enterprise.query.count()
    产品数量 = Product.query.count()
    需求数量 = ClientNeed.query.count()
    撮合数量 = MatchProgress.query.count()

    核心模块 = [
        {"名称": "企业库管理", "说明": "维护国内企业基础信息、联系人及出海目标。", "链接": "#"},
        {"名称": "产品管理", "说明": "管理企业产品信息、品类与产品描述。", "链接": "#"},
        {"名称": "资质证照", "说明": "维护企业相关资质证照、编号和有效期。", "链接": "#"},
        {"名称": "外资客户需求", "说明": "记录海外客户需求与目标采购方向。", "链接": "#"},
        {"名称": "撮合进展", "说明": "跟踪撮合过程、阶段状态与跟进记录。", "链接": "#"},
        {"名称": "归档文件", "说明": "统一存放项目过程文档与归档资料。", "链接": "#"},
    ]

    return render_template(
        "dashboard.html",
        企业数量=企业数量,
        产品数量=产品数量,
        需求数量=需求数量,
        撮合数量=撮合数量,
        核心模块=核心模块,
    )


@app.route("/登录", methods=["GET", "POST"])
def 登录():
    if request.method == "POST":
        用户名 = request.form.get("用户名", "").strip()
        密码 = request.form.get("密码", "").strip()

        用户 = User.query.filter_by(用户名=用户名, 密码=密码).first()
        if 用户:
            session["用户"] = 用户.用户名
            flash("登录成功", "success")
            return redirect(url_for("dashboard"))

        flash("用户名或密码错误", "danger")

    return render_template("login.html")


@app.route("/退出")
def 退出():
    session.pop("用户", None)
    flash("已退出登录", "info")
    return redirect(url_for("登录"))


@app.cli.command("init-db")
def init_db_command():
    """初始化数据库（可选：flask init-db）。"""

    db.create_all()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(用户名="admin").first():
            db.session.add(User(用户名="admin", 密码="admin123"))
            db.session.commit()

    app.run(host="0.0.0.0", port=5000, debug=True)
