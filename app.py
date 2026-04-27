from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

from models import Demand, Enterprise, MatchRecord, Product, User, db

BASE_DIR = Path(__file__).resolve().parent


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "replace-with-a-secure-secret-key"
    # 当前默认 SQLite，后续可直接替换为 PostgreSQL 连接串，例如：
    # postgresql+psycopg2://user:password@localhost:5432/trade_agent
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'trade_agent.db'}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    @app.route("/")
    def dashboard():
        企业数量 = Enterprise.query.count()
        产品数量 = Product.query.count()
        需求数量 = Demand.query.count()
        撮合数量 = MatchRecord.query.count()

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

            用户 = User.query.filter_by(username=用户名, password=密码).first()
            if 用户:
                session["用户"] = 用户.username
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

        init_db(app)

    return app


def init_db(app):
    """初始化数据库与基础账号。"""

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password="admin123"))
            db.session.commit()


app = create_app()

if __name__ == "__main__":
    init_db(app)
    app.run(host="0.0.0.0", port=5000, debug=True)
