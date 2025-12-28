"""
Discord Bot for Manual Arbitrage Scans
Allows triggering GitHub Actions workflows from Discord with /scan command
"""
import discord
from discord import app_commands
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = 'Paulkelvin/FREEDOM'

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.command(name="scan", description="🔍 Run immediate arbitrage scan (5 minutes, ~10 API credits)")
async def scan_now(interaction: discord.Interaction):
    """Trigger a 5-minute arbitrage scan"""
    await interaction.response.defer(ephemeral=False)
    
    # Trigger GitHub Actions workflow via repository_dispatch
    response = requests.post(
        f'https://api.github.com/repos/{GITHUB_REPO}/dispatches',
        headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        },
        json={'event_type': 'scan_now'}
    )
    
    if response.status_code == 204:
        embed = discord.Embed(
            title="✅ Arbitrage Scan Started",
            description=(
                "**Duration:** 5 minutes\n"
                "**Sport:** Basketball NBA\n"
                "**API Cost:** ~10 credits\n\n"
                "Results will appear in this channel within 5-10 minutes if arbitrage opportunities found.\n\n"
                "💡 Check workflow status: https://github.com/Paulkelvin/FREEDOM/actions"
            ),
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Scan Failed",
            description=(
                f"**Error:** {response.status_code}\n"
                f"**Details:** {response.text}\n\n"
                "Check your GITHUB_TOKEN in .env file"
            ),
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


@tree.command(name="scan_status", description="📊 Check API quota and system status")
async def scan_status(interaction: discord.Interaction):
    """Show current API quota and last scan results"""
    await interaction.response.defer(ephemeral=True)
    
    # Get workflow runs from GitHub API
    response = requests.get(
        f'https://api.github.com/repos/{GITHUB_REPO}/actions/runs?per_page=1',
        headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
    )
    
    if response.status_code == 200:
        runs = response.json().get('workflow_runs', [])
        if runs:
            last_run = runs[0]
            status = last_run['status']
            conclusion = last_run.get('conclusion', 'running')
            
            status_emoji = {
                'completed': '✅',
                'in_progress': '🔄',
                'queued': '⏳'
            }.get(status, '❓')
            
            embed = discord.Embed(
                title="📊 System Status",
                description=(
                    f"**Last Scan:** {status_emoji} {conclusion.title()}\n"
                    f"**Started:** {last_run['created_at'][:10]}\n"
                    f"**Workflow:** {last_run['name']}\n\n"
                    "[View Details on GitHub](https://github.com/Paulkelvin/FREEDOM/actions)"
                ),
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="📊 System Status",
                description="No scans found. Use `/scan` to start your first scan!",
                color=discord.Color.orange()
            )
    else:
        embed = discord.Embed(
            title="❌ Status Check Failed",
            description=f"Could not fetch workflow status: {response.status_code}",
            color=discord.Color.red()
        )
    
    await interaction.followup.send(embed=embed, ephemeral=True)


@client.event
async def on_ready():
    await tree.sync()
    print(f'✅ Discord bot logged in as {client.user}')
    print(f'📡 Slash commands synced: /scan, /scan_status')
    print(f'🔗 Monitoring GitHub repo: {GITHUB_REPO}')
    print(f'⚠️ Keep this window open to receive Discord commands')


if __name__ == '__main__':
    if not DISCORD_BOT_TOKEN:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in .env file")
        print("Set up your Discord bot at: https://discord.com/developers/applications")
        exit(1)
    
    if not GITHUB_TOKEN:
        print("❌ ERROR: GITHUB_TOKEN not found in .env file")
        print("Create token at: https://github.com/settings/tokens")
        exit(1)
    
    print("🤖 Starting Discord bot...")
    client.run(DISCORD_BOT_TOKEN)
