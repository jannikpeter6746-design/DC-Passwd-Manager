"""
Database models for the Discord Password Manager.
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Category(db.Model):
    """A password category associated with a Discord guild."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    discord_category_id = db.Column(db.String(32), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    passwords = db.relationship("Password", back_populates="category", cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint("guild_id", "name", name="uq_guild_category"),)

    def __repr__(self):
        return f"<Category {self.name!r} guild={self.guild_id}>"


class Password(db.Model):
    """An encrypted password entry within a category."""

    __tablename__ = "passwords"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    username_email = db.Column(db.String(255), nullable=False)
    encrypted_password = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    # Comma-separated role IDs that may view this password
    allowed_roles = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    category = db.relationship("Category", back_populates="passwords")

    def allowed_role_ids(self):
        """Return the list of allowed role IDs as strings."""
        if not self.allowed_roles:
            return []
        return [r.strip() for r in self.allowed_roles.split(",") if r.strip()]

    def __repr__(self):
        return f"<Password id={self.id} user={self.username_email!r}>"
