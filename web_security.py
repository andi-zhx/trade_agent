"""Authentication and HTTP safeguards shared by local and hosted deployments."""
from datetime import timedelta, timezone
import hashlib
import os
from pathlib import Path
import secrets
from zoneinfo import ZoneInfo

from flask import abort, g, jsonify, redirect, render_template, request, session, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import StaleDataError
from werkzeug.middleware.proxy_fix import ProxyFix

from models import User, db


def password_stamp(user):
    return hashlib.sha256(f"{user.password}|{user.updated_at}".encode()).hexdigest()


def configure(app, root, overrides):
    production = os.getenv("TRADE_ENV") == "production"
    data_root = Path(os.getenv("TRADE_DATA_DIR", str(root))).resolve()
    app.config.update(
        PRODUCTION=production,
        DATA_ROOT=data_root,
        SECRET_KEY=os.getenv("TRADE_SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{data_root / 'trade_agent.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"timeout": 30}},
        UPLOAD_ROOT=data_root / "uploads" / "企业库",
        UPLOAD_ENTERPRISE_ROOT=data_root / "uploads" / "企业库",
        BACKUP_ROOT=data_root / "backups",
        DATABASE_BACKUP_ROOT=data_root / "backups" / "database",
        FILES_BACKUP_ROOT=data_root / "backups" / "files",
        BACKUP_RETENTION_DAYS=30,
        BACKUP_RETENTION_COUNT=30,
        BACKUP_INTERVAL_SECONDS=3600,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        WTF_CSRF_TIME_LIMIT=8 * 60 * 60,
        MAX_CONTENT_LENGTH=100 * 1024 * 1024,
        RATELIMIT_STORAGE_URI="memory://",
    )
    app.config.update(overrides or {})
    if overrides and "DATA_ROOT" in overrides:
        root_override = Path(overrides["DATA_ROOT"])
        defaults = {
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{root_override / 'trade_agent.db'}",
            "UPLOAD_ROOT": root_override / "uploads" / "企业库",
            "UPLOAD_ENTERPRISE_ROOT": root_override / "uploads" / "企业库",
            "BACKUP_ROOT": root_override / "backups",
            "DATABASE_BACKUP_ROOT": root_override / "backups" / "database",
            "FILES_BACKUP_ROOT": root_override / "backups" / "files",
        }
        app.config.update({key: value for key, value in defaults.items() if key not in overrides})
    data_root = Path(app.config["DATA_ROOT"])
    data_root.mkdir(parents=True, exist_ok=True)
    if app.config["PRODUCTION"]:
        if len(app.config.get("SECRET_KEY") or "") < 32:
            raise RuntimeError("生产环境必须设置至少 32 字符的 TRADE_SECRET_KEY。")
        if os.getenv("TRADE_TRUST_PROXY") == "1":
            app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    elif not app.config.get("SECRET_KEY"):
        if app.config.get("TESTING"):
            app.config["SECRET_KEY"] = secrets.token_hex(32)
        else:
            key_file = data_root / ".secret_key"
            try:
                fd = os.open(key_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                pass
            else:
                with os.fdopen(fd, "w") as stream:
                    stream.write(secrets.token_hex(32))
            app.config["SECRET_KEY"] = key_file.read_text().strip()


def install(app):
    CSRFProtect(app)
    @app.template_filter("localtime")
    def localtime(value, pattern="%Y-%m-%d %H:%M"):
        if value is None:
            return ""
        return value.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).strftime(pattern)
    limiter = Limiter(key_func=get_remote_address, app=app, default_limits=[])
    app.extensions["login_limiter"] = limiter
    app.view_functions["登录"] = limiter.limit("10 per minute", methods=["POST"])(app.view_functions["登录"])

    @app.before_request
    def authenticate():
        if request.endpoint in {"登录", "static", "healthz"}:
            return None
        user = User.query.filter_by(username=session.get("用户")).first() if session.get("用户") else None
        if user is None or session.get("auth_stamp") != password_stamp(user):
            # Unauthenticated auxiliary requests must not rotate the login CSRF token.
            if session.get("用户"):
                session.clear()
            return redirect(url_for("登录"))
        g.user = user
        session["角色"] = user.role

    @app.get("/healthz")
    def healthz():
        try:
            db.session.execute(text("SELECT id FROM users LIMIT 1"))
            return jsonify(status="ok")
        except Exception:
            db.session.rollback()
            return jsonify(status="unavailable"), 503

    @app.after_request
    def response_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        if app.config["PRODUCTION"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        # Legacy endpoints accept return URLs; never redirect a member off-site.
        location = response.headers.get("Location", "")
        if location and (not location.startswith("/") or location.startswith("//") or "\\" in location):
            response.headers["Location"] = url_for("enterprise_list")
        return response

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return render_template("request_error.html", message="页面已过期或表单验证失败。请返回原页面复制未保存的内容，再刷新后提交。"), 400

    @app.errorhandler(429)
    def rate_limit(_error):
        return render_template("request_error.html", message="登录尝试过于频繁，请稍后再试。"), 429

    @app.errorhandler(StaleDataError)
    @app.errorhandler(IntegrityError)
    def conflicting_write(_error):
        db.session.rollback()
        return render_template("request_error.html", message="资料已被修改或编号重复，本次操作未保存。请返回原页面保留输入，另开页面核对最新资料。"), 409

    @app.errorhandler(OperationalError)
    def unavailable_storage(_error):
        db.session.rollback()
        app.logger.exception("数据库操作失败")
        return render_template("request_error.html", message="存储暂时不可用，本次操作未保存。请保留输入，稍后重试。"), 503


def require_admin():
    if not getattr(g, "user", None) or g.user.role != "管理员":
        abort(403)
