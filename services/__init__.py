import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config import DISCORD_ADMIN_ROLE, DISCORD_ALLOWED_USER_IDS, DISCORD_BOT_TOKEN, DISCORD_GUILD_ID
from services.command_logger import log_command
from services.discord_formatter import build_embed
from services.discord_notifications import send_discord_alert
from services.github_service import fetch_repo_summary
from services.system_service import get_system_status
from bot import backup_task, github_monitor_task, system_health_task


ALLOWED_USERS = {item.strip() for item in (DISCORD_ALLOWED_USER_IDS or "").split(",") if item.strip()}


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as exc:
            print(f"Failed to sync commands: {exc}")

    async def has_admin_access(self, interaction):
        if str(interaction.user.id) in ALLOWED_USERS:
            return True

        if not interaction.guild:
            return False

        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            return False

        role_names = {role.name.lower() for role in member.roles}
        return DISCORD_ADMIN_ROLE.lower() in role_names


bot = DiscordBot()


async def log_interaction(interaction, command_name, result, success=True):
    user_name = getattr(interaction.user, "display_name", str(interaction.user))
    log_command("discord", command_name, user_name, result, success)


@bot.tree.command(name="status", description="Check AI-Bot status")
async def status(interaction: discord.Interaction):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "status", "Unauthorized access", False)
        return

    embed = build_embed("AI-Bot Status", "✅ AI-Bot is running and monitoring tasks.", color=0x00AA00)
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_interaction(interaction, "status", "Status displayed", True)


@bot.tree.command(name="github", description="View GitHub repository info")
async def github(interaction: discord.Interaction):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "github", "Unauthorized access", False)
        return

    repo = fetch_repo_summary("vinit-cyber-lab/AI-Bot")
    if not repo:
        await interaction.response.send_message("❌ GitHub data unavailable.", ephemeral=True)
        await log_interaction(interaction, "github", "GitHub data unavailable", False)
        return

    embed = build_embed(
        repo.get("full_name", "AI-Bot"),
        repo.get("description", "No description available."),
        color=0x5865F2,
        fields=[
            {"name": "Stars", "value": str(repo.get("stargazers_count", 0)), "inline": True},
            {"name": "Forks", "value": str(repo.get("forks_count", 0)), "inline": True},
            {"name": "Open Issues", "value": str(repo.get("open_issues_count", 0)), "inline": True},
            {"name": "Last Push", "value": str(repo.get("pushed_at", "N/A")), "inline": False},
        ],
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_interaction(interaction, "github", "GitHub stats displayed", True)


@bot.tree.command(name="health", description="Check system health")
async def health(interaction: discord.Interaction):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "health", "Unauthorized access", False)
        return

    stats = get_system_status()
    if not stats:
        await interaction.response.send_message("❌ System health unavailable.", ephemeral=True)
        await log_interaction(interaction, "health", "System health unavailable", False)
        return

    embed = build_embed(
        "System Health",
        "Live system health metrics",
        color=0x00AA00,
        fields=[
            {"name": "CPU", "value": f"{stats.get('cpu_percent', 0)}%", "inline": True},
            {"name": "Memory", "value": f"{stats.get('memory_percent', 0)}%", "inline": True},
            {"name": "Disk", "value": f"{stats.get('disk_percent', 0)}%", "inline": True},
            {"name": "Platform", "value": str(stats.get("platform", "N/A")), "inline": False},
        ],
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)
    await log_interaction(interaction, "health", "Health stats displayed", True)


@bot.tree.command(name="backup", description="Trigger a backup task")
async def backup_cmd(interaction: discord.Interaction):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "backup", "Unauthorized access", False)
        return

    try:
        path = backup_task()
        await interaction.response.send_message(f"✅ Backup triggered successfully: `{path}`", ephemeral=True)
        await log_interaction(interaction, "backup", f"Backup created at {path}", True)
    except Exception as exc:
        await interaction.response.send_message(f"❌ Backup failed: {exc}", ephemeral=True)
        await log_interaction(interaction, "backup", f"Backup failed: {exc}", False)


@bot.tree.command(name="logs", description="View recent bot logs")
async def logs(interaction: discord.Interaction):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "logs", "Unauthorized access", False)
        return

    try:
        with open("logs/bot.log", "r", encoding="utf-8") as file:
            content = "".join(file.readlines()[-20:]) or "No logs available yet."
        await interaction.response.send_message(f"```\n{content}\n```", ephemeral=True)
        await log_interaction(interaction, "logs", "Logs displayed", True)
    except Exception:
        await interaction.response.send_message("No logs found yet.", ephemeral=True)
        await log_interaction(interaction, "logs", "No logs found", False)


@bot.tree.command(name="run", description="Run a bot task")
async def run_task(interaction: discord.Interaction, task_name: str):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "run", "Unauthorized access", False)
        return

    task_name = task_name.lower().strip()
    if task_name == "github":
        try:
            github_monitor_task()
            await interaction.response.send_message("✅ GitHub task executed.", ephemeral=True)
            await log_interaction(interaction, "run", "GitHub task executed", True)
        except Exception as exc:
            await interaction.response.send_message(f"❌ GitHub task failed: {exc}", ephemeral=True)
            await log_interaction(interaction, "run", f"GitHub task failed: {exc}", False)
        return

    if task_name == "health":
        try:
            system_health_task()
            await interaction.response.send_message("✅ Health task executed.", ephemeral=True)
            await log_interaction(interaction, "run", "Health task executed", True)
        except Exception as exc:
            await interaction.response.send_message(f"❌ Health task failed: {exc}", ephemeral=True)
            await log_interaction(interaction, "run", f"Health task failed: {exc}", False)
        return

    if task_name == "backup":
        try:
            path = backup_task()
            await interaction.response.send_message(f"✅ Backup task executed: `{path}`", ephemeral=True)
            await log_interaction(interaction, "run", f"Backup task executed: {path}", True)
        except Exception as exc:
            await interaction.response.send_message(f"❌ Backup task failed: {exc}", ephemeral=True)
            await log_interaction(interaction, "run", f"Backup task failed: {exc}", False)
        return

    await interaction.response.send_message("❌ Unknown task. Use: github, health, backup", ephemeral=True)
    await log_interaction(interaction, "run", f"Unknown task: {task_name}", False)


@bot.tree.command(name="help", description="Show Discord command list")
async def help_cmd(interaction: discord.Interaction):
    if not await bot.has_admin_access(interaction):
        await interaction.response.send_message("❌ Unauthorized access.", ephemeral=True)
        await log_interaction(interaction, "help", "Unauthorized access", False)
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
    await interaction.response.send_message(help_text, ephemeral=True)
    await log_interaction(interaction, "help", "Help listed", True)


if __name__ == "__main__":
    if not DISCORD_BOT_TOKEN:
        print("DISCORD_BOT_TOKEN is missing. Discord bot is disabled.")
    else:
        bot.run(DISCORD_BOT_TOKEN)
