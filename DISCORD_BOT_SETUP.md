# Discord Bot Setup Guide

## 🎯 What This Does

Type `/scan` in your Discord server → Bot triggers GitHub Actions → Arbitrage scan runs → Results sent to Discord

---

## 📋 Setup Steps (5 Minutes)

### **Step 1: Create Discord Bot**

1. Go to: https://discord.com/developers/applications
2. Click **"New Application"** → Name it "Arbitrage Scanner"
3. Go to **"Bot"** tab → Click **"Add Bot"**
4. **Copy the bot token** (you'll need this for .env)
5. Enable these settings:
   - ✅ **MESSAGE CONTENT INTENT**
   - ✅ **SERVER MEMBERS INTENT**

---

### **Step 2: Create GitHub Token**

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Name: "Discord Bot Workflow Trigger"
4. Expiration: **No expiration** (or 1 year)
5. Check **`repo`** scope (Full control of repositories)
6. Click **"Generate token"**
7. **Copy the token** (you'll need this for .env)

---

### **Step 3: Add Bot to Your Discord Server**

1. Back in Discord Developer Portal → Go to **"OAuth2"** → **"URL Generator"**
2. Select scopes:
   - ✅ **bot**
   - ✅ **applications.commands**
3. Select bot permissions:
   - ✅ **Send Messages**
   - ✅ **Use Slash Commands**
4. **Copy the generated URL** at bottom
5. **Paste in browser** → Select your server → Authorize

---

### **Step 4: Configure .env File**

Open your `.env` file and add:

```env
# Your existing settings
ODDS_API_KEY=your_existing_key
DISCORD_WEBHOOK_URL=your_existing_webhook

# NEW: Add these two lines
DISCORD_BOT_TOKEN=paste_bot_token_from_step1_here
GITHUB_TOKEN=paste_github_token_from_step2_here
```

---

### **Step 5: Install Discord Library**

```powershell
pip install discord.py
```

---

### **Step 6: Run the Bot**

```powershell
python discord_bot.py
```

**You should see:**
```
✅ Discord bot logged in as Arbitrage Scanner#1234
📡 Slash commands synced: /scan, /scan_status
🔗 Monitoring GitHub repo: Paulkelvin/FREEDOM
⚠️ Keep this window open to receive Discord commands
```

---

## 🎮 How to Use

### **Trigger a Scan:**
1. Open your Discord server
2. Type `/scan` in any channel
3. Bot responds: "✅ Arbitrage Scan Started"
4. Wait 5-10 minutes
5. Check webhook channel for results

### **Check Status:**
- Type `/scan_status` to see last scan results

---

## 💡 How It Works

```
You type /scan in Discord
         ↓
Discord bot catches command
         ↓
Bot calls GitHub API
         ↓
GitHub Actions starts workflow
         ↓
Workflow runs main.py for 5 min
         ↓
Results sent to Discord webhook
```

---

## ⚙️ Bot Commands

| Command | Description | Cost |
|---------|-------------|------|
| `/scan` | Run 5-minute scan | ~10 credits |
| `/scan_status` | Check last scan results | Free |

---

## 🔧 Troubleshooting

**Bot not responding to /scan?**
- Make sure bot is online (green dot in Discord)
- Check MESSAGE CONTENT INTENT is enabled
- Run `python discord_bot.py` again

**"Invalid token" error?**
- Double-check DISCORD_BOT_TOKEN in .env
- Make sure you copied the bot token (not client secret)

**"403 Forbidden" from GitHub?**
- Check GITHUB_TOKEN has `repo` permission
- Token might be expired

---

## 📊 API Credit Usage

**With Discord bot:**
- Manual scans: ~10 credits each
- You can do 50 scans/month (500 credits ÷ 10)
- Or mix: 4 auto Saturday runs (240 credits) + 26 manual scans

**Recommended:**
- Use manual `/scan` when you see interesting games
- Let Saturday auto-runs handle routine monitoring

---

## ⚠️ Important Notes

- **Keep the bot running** - Close the PowerShell window = bot goes offline
- **Run on your PC** - No cloud hosting needed (free!)
- **One scan at a time** - Wait for previous scan to finish
- **Bot only works when your PC is on**

---

## 🚀 Quick Start

```powershell
# 1. Install dependency
pip install discord.py

# 2. Add tokens to .env file
# (DISCORD_BOT_TOKEN and GITHUB_TOKEN)

# 3. Run bot
python discord_bot.py

# 4. In Discord, type: /scan
```

**That's it!** The bot will trigger GitHub Actions and results appear in your webhook channel.
