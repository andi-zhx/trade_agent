"""Small shared-library membership: admin creates users; no public signup."""
import os
import re

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import AuditLog, User, db
from web_security import password_stamp, require_admin

members = Blueprint("members", __name__)


def valid_password(password):
    return 12 <= len(password) <= 128 and password not in {"admin123", "user123"}


def bootstrap_users(app):
    if app.config["PRODUCTION"]:
        username = os.getenv("TRADE_ADMIN_USERNAME", "admin")
        password = os.getenv("TRADE_ADMIN_PASSWORD", "")
        admin = User.query.filter_by(username=username).first()
        insecure_admin = admin and check_password_hash(admin.password, "admin123")
        if admin is None or insecure_admin:
            if not valid_password(password):
                raise RuntimeError("首次上线或迁移默认账号时，必须设置至少 12 字符的 TRADE_ADMIN_PASSWORD。")
            if admin is None:
                admin = User(username=username, role="管理员")
                db.session.add(admin)
            admin.password = generate_password_hash(password)
        # Do not silently enable public demo credentials when migrating local data.
        for user in User.query.all():
            if any(check_password_hash(user.password, value) for value in ("admin123", "user123")):
                user.soft_delete("system")
        if not User.query.filter_by(role="管理员").count():
            raise RuntimeError("至少需要一个启用的管理员账号。")
    else:
        for username, password, role in [("admin", "admin123", "管理员"), ("user", "user123", "普通用户")]:
            existing = User.query.execution_options(include_deleted=True).filter_by(username=username).first()
            if existing is None:
                db.session.add(User(username=username, password=generate_password_hash(password), role=role))
    db.session.commit()


@members.route("/account/password", methods=["GET", "POST"])
def password():
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        if not check_password_hash(g.user.password, request.form.get("current_password", "")):
            flash("当前密码不正确。", "danger")
        elif not valid_password(new_password) or new_password != request.form.get("confirm_password"):
            flash("新密码须为 12–128 个字符，且两次输入一致。", "danger")
        else:
            g.user.password = generate_password_hash(new_password)
            db.session.add(AuditLog(action="修改密码", target_type="user", target_id=g.user.id, user_name=g.user.username))
            db.session.commit()
            session["auth_stamp"] = password_stamp(g.user)
            flash("密码已更新；其他设备的登录已失效。", "success")
            return redirect(url_for("entry.home"))
    return render_template("account_password.html")


@members.route("/members", methods=["GET", "POST"])
def manage():
    require_admin()
    if request.method == "POST":
        action = request.form.get("action", "create")
        try:
            if action == "create":
                username = request.form.get("username", "").strip()
                password = request.form.get("password", "")
                if not re.fullmatch(r"[\w.@-]{2,50}", username) or not valid_password(password):
                    raise ValueError("用户名须为 2–50 个字母、数字或 . @ _ -，密码须为 12–128 个字符。")
                user = User(username=username, password=generate_password_hash(password), role="普通用户")
                db.session.add(user)
                db.session.flush()
            else:
                user = User.query.execution_options(include_deleted=True).filter_by(id=request.form.get("user_id", type=int)).first_or_404()
                if user.role == "管理员":
                    raise ValueError("管理员请使用“修改密码”；此处只管理普通成员。")
                if action == "toggle":
                    user.is_deleted = not user.is_deleted
                elif action == "reset":
                    password = request.form.get("password", "")
                    if not valid_password(password):
                        raise ValueError("新密码须为 12–128 个字符。")
                    user.password = generate_password_hash(password)
                else:
                    raise ValueError("未知操作。")
            db.session.add(AuditLog(action=f"成员管理:{action}", target_type="user", target_id=user.id, user_name=g.user.username))
            db.session.commit()
            flash("成员设置已保存。", "success")
            return redirect(url_for("members.manage"))
        except IntegrityError:
            db.session.rollback()
            flash("该用户名已存在（包括停用的账号）。", "danger")
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
    users = User.query.execution_options(include_deleted=True).order_by(User.id).all()
    return render_template("members.html", users=users)
