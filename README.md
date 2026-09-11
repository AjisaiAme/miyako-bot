#  Miyako Bot

A simple discord bot with basic server utilities... and landmines.

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
git clone https://github.com/AjisaiAme/miyako-bot.git

# Enter directory
cd miyako-bot

# Install dependencies
pip install discord.py python-dotenv aiohttp
npm install
```

To run Miyako:

```
python main.py
```

### Configuration

- Create `.env` on the project root.
- Copy and paste your Discord bot token. Generate one at the [Discord Developer Portal](https://discord.com/developers/applications).
```
DISCORD_BOT_TOKEN=token_here
PREFIX=m! # default prefix
```

- The bot must have the following **Priviledged Gateway Intents**
  - Presence Intent
  - Server Members Intent
  - Message Content Intent
  
### Persistence

Make sure that **SQLite** is installed on your system as it is needed to initialize the `miyako_data.db` file, where landmine statistics, channel configurations, and active mine counts are stored.

### Commands

Miyako operates with the `m!` prefix.

| Command    | Alias | Description                               | Usage                            |
| :--------- | :---- | :---------------------------------------- | :------------------------------- |
| `m!roll`   | `m!d` | Rolls dice with modifiers (max 50d1000).  | `m!roll 2d20 + 5`                |
| `m!poll`   | -     | Creates an interactive button-based poll. | `m!poll "Question" Opt1 Opt2`    |
| `m!timer`  | -     | Sets a countdown timer (max 6 hours).     | `m!timer 10 Coffee Break`        |
| `m!choose` | -     | Randomly picks an item from a list.       | `m!choose Apple, Orange, Banana` |
| `m!flip`   | -     | Flips a coin with an optional guess.      | `m!flip heads`                   |
| `m!random` | -     | Generates a random number in a range.     | `m!random 1 100`                 |
| `m!rate`   | -     | Ask the bot to rate something from 1-10.  | `m!rate this code`               |
| `m!help`   | `m!h` | Displays the help menu for all commands.  | `m!help [command]`               |

### Final Fantasy XIV

| Command | Alias | Description | Usage |
| :------ | :---- | :---------- | :---- |
| `m!frontline` | `m!fl` | Shows the current Frontline map and upcoming rotation. | `m!fl` |

### Landmine Game

Based on a funny bit from [Max0r's server](https://x.com/realMax0r/status/1982196340387188780). When enabled, landmines can drop with a 1% chance every time a message is sent, and another 1% chance to detonate it when present to time them out for 30 seconds (up to 3 minutes).

To avoid being too annoying, the module must be **enabled per channel** by a server admin.

|Command|Description|Usage|
|---|---|---|
|`m!lm allow`|Enables landmines in the current channel.|`m!lm allow`|
|`m!lm restrict`|Disables landmines and clears all active mines.|`m!lm restrict`|
|`m!lm config`|View or change per‑channel settings.|`m!lm config [setting] [value]`|
|`m!lm clear`|Clear all active mines from the current channel.|`m!lm clear`|
|`m!lm check`|Shows the number of active mines in the channel.|`m!lm check`|
|`m!lm drop [1-10]`|Manually places at a 10s cooldown).|`m!lm drop 5`|
|`m!lm step`|Please don't do this... (5s cooldown).|`m!lm step`|
|`m!lm stats [@user]`|Displays landmine statistics for a user.|`m!lm stats @Ajisai`|
|`m!lm serverstats`|Shows server‑wide landmine statistics.|`m!lm serverstats`|
|`m!lm top`|Global leaderboards of landmine statistics.|`m!lm top`|
|`m!lm rateup`|Checks if the trigger rate‑up is currently active.|`m!lm rateup`|
