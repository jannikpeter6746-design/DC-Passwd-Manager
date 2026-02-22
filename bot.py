"""DC-Passwd-Manager – Discord Password Manager Bot

Commands (DM only for security):
  !addpass   <service> <password>  – Save / update a password
  !getpass   <service>             – Retrieve a password
  !listpass                        – List all saved service names
  !deletepass <service>            – Delete a saved password
  !help                            – Show this help message

All passwords are encrypted with a per-user Fernet key derived from
the BOT_SECRET_KEY environment variable so that nothing is stored in
plain text.
"""

import os
import base64
import hashlib
import logging

import discord
from discord.ext import commands
from cryptography.fernet import Fernet

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Encryption helpers
# ---------------------------------------------------------------------------

def _user_fernet(user_id: str) -> Fernet:
    """Return a Fernet instance keyed to this user + the bot secret."""
    secret_key = os.environ.get("BOT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("BOT_SECRET_KEY environment variable is not set.")
    secret = secret_key.encode() + user_id.encode()
    key = base64.urlsafe_b64encode(hashlib.sha256(secret).digest())
    return Fernet(key)


def encrypt_password(user_id: str, plaintext: str) -> str:
    f = _user_fernet(user_id)
    return f.encrypt(plaintext.encode()).decode()


def decrypt_password(user_id: str, token: str) -> str:
    f = _user_fernet(user_id)
    return f.decrypt(token.encode()).decode()


# ---------------------------------------------------------------------------
# In-memory storage  {user_id: {service: encrypted_token}}
# The data lives only for the lifetime of this process.  For persistence
# across restarts you can swap this out for a database or file back-end.
# ---------------------------------------------------------------------------
_store: dict[str, dict[str, str]] = {}


# ---------------------------------------------------------------------------
# Bot setup
# ---------------------------------------------------------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

async def _dm_only_check(ctx: commands.Context) -> bool:
    """Return True only when the command is used in a DM channel."""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.reply(
            "⚠️  Please use password commands in a **direct message** (DM) "
            "with me to keep your passwords private.",
            delete_after=10,
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)
    log.info("DC-Passwd-Manager is ready.")


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.reply(f"❌ Missing argument: `{error.param.name}`. Use `!help` for usage.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.reply("❓ Unknown command. Use `!help` to see available commands.")
    else:
        log.error("Unhandled error in command '%s': %s", ctx.command, error)
        await ctx.reply("⚠️  An unexpected error occurred.")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@bot.command(name="help")
async def help_command(ctx: commands.Context):
    """Show all available commands."""
    embed = discord.Embed(
        title="🔐 DC-Passwd-Manager – Help",
        description=(
            "All password commands must be sent as a **DM** to this bot.\n\n"
            "**Commands**\n"
            "`!addpass <service> <password>` – Save or update a password\n"
            "`!getpass <service>` – Retrieve a saved password\n"
            "`!listpass` – List all saved service names\n"
            "`!deletepass <service>` – Delete a saved password\n"
            "`!help` – Show this message\n\n"
            "⚠️  *Passwords are encrypted and stored **only for the lifetime of "
            "the current bot session**. They will be lost when the bot restarts.*"
        ),
        colour=discord.Colour.blurple(),
    )
    await ctx.reply(embed=embed)


@bot.command(name="addpass")
async def add_password(ctx: commands.Context, service: str, password: str):
    """Save or update a password for a service (DM only)."""
    if not await _dm_only_check(ctx):
        return

    user_id = str(ctx.author.id)
    _store.setdefault(user_id, {})[service] = encrypt_password(user_id, password)

    await ctx.reply(f"✅ Password for **{service}** saved.")

    # Delete the original message so the password is not visible in chat history
    try:
        await ctx.message.delete()
    except discord.HTTPException:
        pass


@bot.command(name="getpass")
async def get_password(ctx: commands.Context, service: str):
    """Retrieve a saved password (DM only)."""
    if not await _dm_only_check(ctx):
        return

    user_id = str(ctx.author.id)
    user_passwords = _store.get(user_id, {})

    if service not in user_passwords:
        await ctx.reply(f"❌ No password found for **{service}**.")
        return

    plaintext = decrypt_password(user_id, user_passwords[service])
    msg = await ctx.reply(f"🔑 Password for **{service}**: `{plaintext}`")
    # Auto-delete after 30 seconds to minimise exposure in chat history
    await msg.delete(delay=30)


@bot.command(name="listpass")
async def list_passwords(ctx: commands.Context):
    """List all saved service names (DM only)."""
    if not await _dm_only_check(ctx):
        return

    user_id = str(ctx.author.id)
    user_passwords = _store.get(user_id, {})

    if not user_passwords:
        await ctx.reply("📭 You have no passwords saved yet.")
        return

    services = "\n".join(f"• {s}" for s in sorted(user_passwords.keys()))
    embed = discord.Embed(
        title="📋 Saved services",
        description=services,
        colour=discord.Colour.green(),
    )
    await ctx.reply(embed=embed)


@bot.command(name="deletepass")
async def delete_password(ctx: commands.Context, service: str):
    """Delete a saved password (DM only)."""
    if not await _dm_only_check(ctx):
        return

    user_id = str(ctx.author.id)
    user_passwords = _store.get(user_id, {})

    if service not in user_passwords:
        await ctx.reply(f"❌ No password found for **{service}**.")
        return

    del user_passwords[service]
    await ctx.reply(f"🗑️  Password for **{service}** deleted.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_TOKEN environment variable is not set. "
            "Add it as a GitHub Actions secret (see README)."
        )
    secret_key = os.environ.get("BOT_SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "BOT_SECRET_KEY environment variable is not set. "
            "Add it as a GitHub Actions secret (see README)."
        )

    bot.run(token, log_handler=None)
