import os
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_ADMIN_ROLE,
    DISCORD_ALLOWED_USER_IDS,
)
from services.github_service import fetch_repo_summary
from services.system_service import get_system_status
from bot import backup_task, github_monitor_task, system_health_task

load_dotenv()


def normalize_allowed_users(value: str):
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


ALLOWED_USER_IDS = normalize_allowed_users(DISCORD_ALLOWED_USER_IDS)


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Discord bot logged in as {self.user} ({self.user.id})")
        if DISCORD_GUILD_ID:
            guild = self.get_guild(DISCORD_GUILD_ID)
            if guild:
                print(f"Connected to guild: {guild.name}")

    async def has_admin_access(self, ctx):
        if not DISCORD_ADMIN_ROLE:
            return True

        if str(ctx.author.id) in ALLOWED_USER_IDS:
            return True

        member = ctx.guild.get_member(ctx.author.id) if ctx.guild else None
        if not member:
            return False

        role_names = {role.name.lower() for role in member.roles}
        return DISCORD_ADMIN_ROLE.lower() in role_names


bot = DiscordBot()


@bot.slash_command(name="status", description="Check AI-Bot status")
async def status(ctx):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return
    await ctx.respond("✅ AI-Bot is running and monitoring tasks.", ephemeral=True)


@bot.slash_command(name="github", description="Show GitHub repository stats")
async def github(ctx):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return

    repo = fetch_repo_summary("vinit-cyber-lab/AI-Bot")
    if not repo:
        await ctx.respond("❌ GitHub data unavailable.", ephemeral=True)
        return

    embed = {
        "title": repo.get("full_name", "AI-Bot"),
        "description": repo.get("description", "No description"),
        "color": 0x5865F2,
        "fields": [
            {"name": "Stars", "value": str(repo.get("stargazers_count", 0)), "inline": True},
            {"name": "Forks", "value": str(repo.get("forks_count", 0)), "inline": True},
            {"name": "Open Issues", "value": str(repo.get("open_issues_count", 0)), "inline": True},
            {"name": "Last Push", "value": str(repo.get("pushed_at", "N/A")), "inline": False},
        ],
    }
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="health", description="Check system health")
async def health(ctx):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return

    stats = get_system_status()
    if not stats:
        await ctx.respond("❌ System health unavailable.", ephemeral=True)
        return

    embed = {
        "title": "System Health",
        "color": 0x00AA00,
        "fields": [
            {"name": "CPU", "value": f"{stats.get('cpu_percent', 0)}%", "inline": True},
            {"name": "Memory", "value": f"{stats.get('memory_percent', 0)}%", "inline": True},
            {"name": "Disk", "value": f"{stats.get('disk_percent', 0)}%", "inline": True},
            {"name": "Platform", "value": str(stats.get("platform", "N/A")), "inline": False},
        ],
    }
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="backup", description="Create a backup")
async def backup(ctx):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return

    try:
        backup_task()
        await ctx.respond("✅ Backup task triggered successfully.", ephemeral=True)
    except Exception as exc:
        await ctx.respond(f"❌ Backup failed: {exc}", ephemeral=True)


@bot.slash_command(name="logs", description="View recent bot logs")
async def logs(ctx):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return

    try:
        with open("logs/bot.log", "r", encoding="utf-8") as file:
            lines = file.readlines()[-20:]
        content = "".join(lines) or "No logs available yet."
        await ctx.respond(f"```\n{content}\n```", ephemeral=True)
    except Exception:
        await ctx.respond("No logs found yet.", ephemeral=True)


@bot.slash_command(name="help", description="Show available Discord commands")
async def help_cmd(ctx):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return

    help_text = (
        "**Available commands**\n"
        "/status\n"
        "/github\n"
        "/health\n"
        "/backup\n"
        "/logs\n"
        "/run github\n"
        "/run health\n"
        "/run backup\n"
        "/help"
    )
    await ctx.respond(help_text, ephemeral=True)


@bot.slash_command(name="run", description="Run a bot task")
async def run_task(ctx, task_name: str):
    if not await bot.has_admin_access(ctx):
        await ctx.respond("❌ Unauthorized access.", ephemeral=True)
        return

    task_name = task_name.lower().strip()

    if task_name == "github":
        try:
            github_monitor_task()
            await ctx.respond("✅ GitHub task executed.", ephemeral=True)
        except Exception as exc:
            await ctx.respond(f"❌ GitHub task failed: {exc}", ephemeral=True)
        return

    if task_name == "health":
        try:
            system_health_task()
            await ctx.respond("✅ Health task executed.", ephemeral=True)
        except Exception as exc:
            await ctx.respond(f"❌ Health task failed: {exc}", ephemeral=True)
        return

    if task_name == "backup":
        try:
            backup_task()
            await ctx.respond("✅ Backup task executed.", ephemeral=True)
        except Exception as exc:
            await ctx.respond(f"❌ Backup task failed: {exc}", ephemeral=True)
        return

    await ctx.respond("❌ Unknown task. Use: github, health, backup", ephemeral=True)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("DISCORD_BOT_TOKEN is missing. Discord bot not started.")
    else:
        bot.run(DISCORD_BOT_TOKEN)
