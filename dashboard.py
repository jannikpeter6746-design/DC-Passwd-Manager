"""
Flask web dashboard for the Discord Password Manager.
"""

import os
import secrets
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from models import db, Category, Password
from encryption import encrypt_password, decrypt_password


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def create_app(db_path: str = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), "passwd_manager.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    secret_key = os.environ.get("FLASK_SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError(
            "FLASK_SECRET_KEY is not set. Set it to a long random string in your .env file."
        )
    app.config["SECRET_KEY"] = secret_key

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def login_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login"))
            return f(*args, **kwargs)

        return decorated

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    @login_required
    def index():
        categories = Category.query.all()
        return render_template("index.html", categories=categories)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            expected_user = os.environ.get("DASHBOARD_USERNAME", "admin")
            expected_pass = os.environ.get("DASHBOARD_PASSWORD", "changeme")
            # Constant-time comparison to prevent timing attacks
            user_ok = secrets.compare_digest(username, expected_user)
            pass_ok = secrets.compare_digest(password, expected_pass)
            if user_ok and pass_ok:
                session["logged_in"] = True
                return redirect(url_for("index"))
            flash("Invalid credentials.", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # --- Categories -------------------------------------------------------

    @app.route("/categories")
    @login_required
    def categories():
        all_cats = Category.query.all()
        return render_template("categories.html", categories=all_cats)

    @app.route("/categories/add", methods=["POST"])
    @login_required
    def add_category():
        guild_id = request.form.get("guild_id", "").strip()
        name = request.form.get("name", "").strip()
        if not guild_id or not name:
            flash("Guild ID and name are required.", "danger")
            return redirect(url_for("categories"))
        existing = Category.query.filter_by(guild_id=guild_id, name=name).first()
        if existing:
            flash(f"Category '{name}' already exists for this guild.", "warning")
            return redirect(url_for("categories"))
        cat = Category(guild_id=guild_id, name=name)
        db.session.add(cat)
        db.session.commit()
        flash(f"Category '{name}' created.", "success")
        return redirect(url_for("categories"))

    @app.route("/categories/<int:cat_id>/delete", methods=["POST"])
    @login_required
    def delete_category(cat_id):
        cat = Category.query.get_or_404(cat_id)
        db.session.delete(cat)
        db.session.commit()
        flash(f"Category '{cat.name}' deleted.", "success")
        return redirect(url_for("categories"))

    # --- Passwords --------------------------------------------------------

    @app.route("/categories/<int:cat_id>/passwords")
    @login_required
    def passwords(cat_id):
        cat = Category.query.get_or_404(cat_id)
        entries = []
        for p in cat.passwords:
            entries.append(
                {
                    "id": p.id,
                    "username_email": p.username_email,
                    "notes": p.notes or "",
                    "allowed_roles": p.allowed_roles or "",
                    "created_at": p.created_at,
                }
            )
        return render_template("passwords.html", category=cat, passwords=entries)

    @app.route("/categories/<int:cat_id>/passwords/add", methods=["POST"])
    @login_required
    def add_password(cat_id):
        cat = Category.query.get_or_404(cat_id)
        username_email = request.form.get("username_email", "").strip()
        plain_password = request.form.get("password", "").strip()
        notes = request.form.get("notes", "").strip()
        roles = request.form.get("allowed_roles", "").strip()
        if not username_email or not plain_password:
            flash("Username/email and password are required.", "danger")
            return redirect(url_for("passwords", cat_id=cat_id))
        entry = Password(
            category_id=cat.id,
            username_email=username_email,
            encrypted_password=encrypt_password(plain_password),
            notes=notes or None,
            allowed_roles=roles or None,
        )
        db.session.add(entry)
        db.session.commit()
        flash("Password entry added.", "success")
        return redirect(url_for("passwords", cat_id=cat_id))

    @app.route("/passwords/<int:pw_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_password(pw_id):
        entry = Password.query.get_or_404(pw_id)
        if request.method == "POST":
            entry.username_email = request.form.get("username_email", "").strip()
            plain_password = request.form.get("password", "").strip()
            entry.notes = request.form.get("notes", "").strip() or None
            entry.allowed_roles = request.form.get("allowed_roles", "").strip() or None
            if plain_password:
                entry.encrypted_password = encrypt_password(plain_password)
            db.session.commit()
            flash("Password entry updated.", "success")
            return redirect(url_for("passwords", cat_id=entry.category_id))
        return render_template("edit_password.html", entry=entry)

    @app.route("/passwords/<int:pw_id>/delete", methods=["POST"])
    @login_required
    def delete_password(pw_id):
        entry = Password.query.get_or_404(pw_id)
        cat_id = entry.category_id
        db.session.delete(entry)
        db.session.commit()
        flash("Password entry deleted.", "success")
        return redirect(url_for("passwords", cat_id=cat_id))

    @app.route("/passwords/<int:pw_id>/reveal", methods=["POST"])
    @login_required
    def reveal_password(pw_id):
        entry = Password.query.get_or_404(pw_id)
        try:
            plain = decrypt_password(entry.encrypted_password)
        except Exception:
            return jsonify({"error": "Decryption failed"}), 500
        return jsonify({"password": plain})

    return app
