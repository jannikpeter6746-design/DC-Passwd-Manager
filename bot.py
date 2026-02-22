"""
Discord bot for the Password Manager.

Commands:
  /addcategory <name>
      Creates a Discord category channel and stores it in the database.

  /addpasswd <category> <username_email> <password> <notes> <roles>
      Stores an encrypted password entry visible only to the given role(s).

  /listpasswords <category>
      Lists password entries the caller is authorised to view.

  /deletepassword <id>
      Deletes a password entry by its numeric ID (admin or matching-role only).

  /deletecategory <name>
      Deletes a category and all its passwords (and the Discord channel category).
"""

import os
import json
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

from models import db, Category, Password
from encryption import encrypt_password, decrypt_password, generate_password

# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------

intents = discord.Intents.default()
intents.guilds = True


class PasswordManagerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        guild_id = os.environ.get("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")


bot = PasswordManagerBot()

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _get_app():
    """Import the Flask app lazily to avoid circular imports."""
    from dashboard import create_app
    return create_app()


def _db_context():
    """Return a Flask app-context for database operations inside the bot."""
    app = _get_app()
    return app.app_context()


def _user_role_ids(member: discord.Member):
    return {str(r.id) for r in member.roles}


def _can_view(password: Password, member: discord.Member) -> bool:
    """Return True if the member may view this password entry."""
    allowed = password.allowed_role_ids()
    if not allowed:
        return True  # no restriction → everyone can view
    return bool(_user_role_ids(member) & set(allowed))


# ---------------------------------------------------------------------------
# /addcategory
# ---------------------------------------------------------------------------


@bot.tree.command(name="addcategory", description="Create a new password category")
@app_commands.describe(name="Name of the category (e.g. Google, Server)")
@app_commands.default_permissions(manage_channels=True)
async def addcategory(interaction: discord.Interaction, name: str):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    with _db_context():
        existing = Category.query.filter_by(guild_id=str(guild.id), name=name).first()
        if existing:
            await interaction.followup.send(
                f"❌ Category **{name}** already exists.", ephemeral=True
            )
            return

        # Create Discord category channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False)
        }
        discord_cat = await guild.create_category(name, overwrites=overwrites)

        category = Category(
            guild_id=str(guild.id),
            name=name,
            discord_category_id=str(discord_cat.id),
        )
        db.session.add(category)
        db.session.commit()

    await interaction.followup.send(
        f"✅ Category **{name}** created (Discord category channel: {discord_cat.mention}).",
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# /addpasswd
# ---------------------------------------------------------------------------


@bot.tree.command(name="addpasswd", description="Add a password entry to a category")
@app_commands.describe(
    category="Category name",
    username_email="Username or e-mail address",
    password="The password to store (will be encrypted)",
    notes="Optional notes",
    roles="Comma-separated role names or IDs that may view this entry (leave blank = everyone)",
)
@app_commands.default_permissions(manage_guild=True)
async def addpasswd(
    interaction: discord.Interaction,
    category: str,
    username_email: str,
    password: str,
    notes: str = "",
    roles: str = "",
):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    # Resolve role IDs from names/mentions
    role_ids = []
    if roles.strip():
        for part in roles.split(","):
            part = part.strip().lstrip("<@&").rstrip(">")
            # Try by ID first
            role = None
            if part.isdigit():
                try:
                    role = guild.get_role(int(part))
                except (ValueError, OverflowError):
                    role = None
            # Fall back to name search
            if role is None:
                role = discord.utils.get(guild.roles, name=part)
            if role:
                role_ids.append(str(role.id))
            else:
                await interaction.followup.send(
                    f"❌ Role **{part}** not found.", ephemeral=True
                )
                return

    with _db_context():
        cat = Category.query.filter_by(guild_id=str(guild.id), name=category).first()
        if cat is None:
            await interaction.followup.send(
                f"❌ Category **{category}** does not exist. Use `/addcategory` first.",
                ephemeral=True,
            )
            return

        entry = Password(
            category_id=cat.id,
            username_email=username_email,
            encrypted_password=encrypt_password(password),
            notes=notes or None,
            allowed_roles=",".join(role_ids) if role_ids else None,
        )
        db.session.add(entry)
        db.session.commit()
        entry_id = entry.id

    role_names = ", ".join(f"<@&{r}>" for r in role_ids) if role_ids else "everyone"
    await interaction.followup.send(
        f"✅ Password entry **#{entry_id}** added to category **{category}**.\n"
        f"👤 User: `{username_email}` | 🔑 Visible to: {role_names}",
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# /listpasswords
# ---------------------------------------------------------------------------


@bot.tree.command(name="listpasswords", description="List password entries in a category")
@app_commands.describe(category="Category name")
async def listpasswords(interaction: discord.Interaction, category: str):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    member = interaction.user

    with _db_context():
        cat = Category.query.filter_by(guild_id=str(guild.id), name=category).first()
        if cat is None:
            await interaction.followup.send(
                f"❌ Category **{category}** not found.", ephemeral=True
            )
            return

        visible = [p for p in cat.passwords if _can_view(p, member)]

        if not visible:
            await interaction.followup.send(
                f"🔒 No passwords found in **{category}** that you are allowed to view.",
                ephemeral=True,
            )
            return

        lines = [f"🔐 Passwords in **{category}**:\n"]
        for p in visible:
            plain = decrypt_password(p.encrypted_password)
            role_str = (
                ", ".join(f"<@&{r}>" for r in p.allowed_role_ids())
                if p.allowed_role_ids()
                else "everyone"
            )
            lines.append(
                f"**#{p.id}** | 👤 `{p.username_email}` | 🔑 `{plain}`"
                + (f" | 📝 {p.notes}" if p.notes else "")
                + f" | 🔒 Roles: {role_str}"
            )

    await interaction.followup.send("\n".join(lines), ephemeral=True)


# ---------------------------------------------------------------------------
# /deletepassword
# ---------------------------------------------------------------------------


@bot.tree.command(name="deletepassword", description="Delete a password entry by ID")
@app_commands.describe(entry_id="Numeric ID of the password entry")
@app_commands.default_permissions(manage_guild=True)
async def deletepassword(interaction: discord.Interaction, entry_id: int):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    member = interaction.user

    with _db_context():
        entry = Password.query.get(entry_id)
        if entry is None or entry.category.guild_id != str(guild.id):
            await interaction.followup.send(
                f"❌ Password entry **#{entry_id}** not found.", ephemeral=True
            )
            return

        if not _can_view(entry, member):
            await interaction.followup.send(
                "❌ You do not have permission to delete this entry.", ephemeral=True
            )
            return

        db.session.delete(entry)
        db.session.commit()

    await interaction.followup.send(
        f"✅ Password entry **#{entry_id}** deleted.", ephemeral=True
    )


# ---------------------------------------------------------------------------
# /deletecategory
# ---------------------------------------------------------------------------


@bot.tree.command(name="deletecategory", description="Delete a category and all its passwords")
@app_commands.describe(name="Category name")
@app_commands.default_permissions(manage_channels=True)
async def deletecategory(interaction: discord.Interaction, name: str):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild

    with _db_context():
        cat = Category.query.filter_by(guild_id=str(guild.id), name=name).first()
        if cat is None:
            await interaction.followup.send(
                f"❌ Category **{name}** not found.", ephemeral=True
            )
            return

        # Remove Discord category channel if it still exists
        if cat.discord_category_id:
            discord_cat = guild.get_channel(int(cat.discord_category_id))
            if discord_cat:
                await discord_cat.delete(reason="Deleted via /deletecategory")

        db.session.delete(cat)
        db.session.commit()

    await interaction.followup.send(
        f"✅ Category **{name}** and all its passwords have been deleted.", ephemeral=True
    )


# ---------------------------------------------------------------------------
# /generatepassword
# ---------------------------------------------------------------------------


@bot.tree.command(name="generatepassword", description="Generate a secure random password")
@app_commands.describe(
    length="Length of the password (4-128, default 16)",
    uppercase="Include uppercase letters (default True)",
    numbers="Include digits (default True)",
    symbols="Include punctuation symbols (default True)",
)
async def generatepassword(
    interaction: discord.Interaction,
    length: int = 16,
    uppercase: bool = True,
    numbers: bool = True,
    symbols: bool = True,
):
    await interaction.response.defer(ephemeral=True)
    try:
        password = generate_password(
            length=length, uppercase=uppercase, numbers=numbers, symbols=symbols
        )
    except ValueError as exc:
        await interaction.followup.send(f"❌ {exc}", ephemeral=True)
        return

    char_classes = ["lowercase"]
    if uppercase:
        char_classes.append("uppercase")
    if numbers:
        char_classes.append("numbers")
    if symbols:
        char_classes.append("symbols")

    await interaction.followup.send(
        f"🔑 Generated password (`{', '.join(char_classes)}`, length {length}):\n"
        f"```\n{password}\n```\n"
        "⚠️ This message is ephemeral — only you can see it. Copy it now!",
        ephemeral=True,
    )
