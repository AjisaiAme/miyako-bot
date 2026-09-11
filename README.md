#  Yamashiro Bot

A simple discord bot with basic server utilities... and landmines, Milord.

---

### Requirements
* **Python 3.8+**
* **discord.py**
* **aiohttp**
* **SQLite**

---
### Installation
```bash
# Clone repository
git clone https://github.com/AjisaiAme/yamashiro-bot.git

# Enter directory
cd yamashiro-bot

# Install dependencies
pip install discord.py python-dotenv aiohttp
npm install
```

To run Yamashiro:
```
python main.py
```

### Configuration
- Create `.env` on the project root.
- Copy and paste your Discord bot token. Generate one at the [Discord Developer Portal](https://discord.com/developers/applications).
```
DISCORD_BOT_TOKEN=token_here
PREFIX=y! # default prefix
```
- The bot must have the following **Priviledged Gateway Intents**
  - Presence Intent
  - Server Members Intent
  - Message Content Intent
  
### Persistence
Make sure that **SQLite** is installed on your system as it is needed to initialize `yamashiro_data.db` file, where landmine statistics, channel configurations, and active mine counts are stored. 

### Commands
Yamashiro operates with the `y!` prefix. 

| Command    | Alias | Description                               | Usage                            |
| :--------- | :---- | :---------------------------------------- | :------------------------------- |
| `y!roll`   | `y!d` | Rolls dice with modifiers (max 50d1000).  | `y!roll 2d20 + 5`                |
| `y!poll`   | -     | Creates an interactive button-based poll. | `y!poll "Question" Opt1 Opt2`    |
| `y!timer`  | -     | Sets a countdown timer (max 6 hours).     | `y!timer 10 Coffee Break`        |
| `y!choose` | -     | Randomly picks an item from a list.       | `y!choose Apple, Orange, Banana` |
| `y!flip`   | -     | Flips a coin with an optional guess.      | `y!flip heads`                   |
| `y!random` | -     | Generates a random number in a range.     | `y!random 1 100`                 |
| `y!rate`   | -     | Ask the bot to rate something from 1-10.  | `y!rate this code`               |
| `y!help`   | `y!h` | Displays the help menu for all commands.  | `y!help [command]`               |
| `y!frontline` | `y!fl` | Shows the current Frontline map and upcoming rotation. | `y!fl` |

### Landmine Game

Based on a funny bit from [Max0r's server](https://x.com/realMax0r/status/1982196340387188780). When enabled, landmines can drop with a 1% chance every time a message is sent, and another 1% chance to detonate it when present to time them out for 30 seconds (up to 3 minutes).

To avoid being too annoying, the module must be **enabled per channel** by a server admin.

|Command|Description|Usage|
|---|---|---|
|`y!lm allow`|Enables landmines in the current channel.|`y!lm allow`|
|`y!lm restrict`|Disables landmines and clears all active mines.|`y!lm restrict`|
|`y!lm config`|View or change per‑channel settings.|`y!lm config [setting] [value]`|
|`y!lm clear`|Clear all active mines from the current channel.|`y!lm clear`|
|`y!lm check`|Shows the number of active mines in the channel.|`y!lm check`|
|`y!lm drop [1-10]`|Manually places at a 10s cooldown).|`y!lm drop 5`|
|`y!lm step`|Please don't do this... (5s cooldown).|`y!lm step`|
|`y!lm stats [@user]`|Displays landmine statistics for a user.|`y!lm stats @Ajisai`|
|`y!lm serverstats`|Shows server‑wide landmine statistics.|`y!lm serverstats`|
|`y!lm top`|Global leaderboards of landmine statistics.|`y!lm top`|
|`y!lm rateup`|Checks if the trigger rate‑up is currently active.|`y!lm rateup`|
