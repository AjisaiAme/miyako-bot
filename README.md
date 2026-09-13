# Miyako Bot

A Discord bot with server utilities, games, landmines, and an FFXIV Frontline tracker.

---

### Requirements

* **Python 3.10+**
* A Discord bot application and token

---

### Setup

```bash
git clone https://github.com/AjisaiAme/miyako-bot.git
cd miyako-bot

# Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

# Install dependencies
python -m pip install discord.py aiosqlite python-dotenv
```

Add `.env` in the project root:

```env
DISCORD_BOT_TOKEN=your_token_here
PREFIX=y! # default
```

To run Miyako:
```bash
python main.py
```
```

### Configuration

Create the bot and token in the [Discord Developer Portal](https://discord.com/developers/applications). Enable these **Privileged Gateway Intents**:

* Presence Intent
* Server Members Intent
* Message Content Intent

Invite the bot to your server with permissions to read and send messages, add reactions, and manage messages. The `PREFIX` value in `.env` controls the command prefix; the default is `y!`, while `m!cog` controls require **Manage Server**.

### Run

```bash
python main.py
```

### Persistence

Landmine statistics, channel configurations, and active mine counts are stored in `miyako_data.db`. The database file is created automatically.

### Commands

Miyako operates with the configured prefix (default `y!`).

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

### Server Modules

Server administrators can enable or disable modules per server. These commands require the **Manage Server** permission.

| Command | Description | Usage |
| :------ | :---------- | :---- |
| `m!cog` | Shows the current module status. | `m!cog` |
| `m!cog enable <module>` | Enables a module for this server. | `m!cog enable xiv` |
| `m!cog disable <module>` | Disables a module for this server. | `m!cog disable fun` |

Available modules:

- `utility` – Help, server information, profiles, and status commands
- `fun` – Dice, polls, timers, games, and ratings
- `landmine` – The landmine game and its statistics
- `xiv` – Final Fantasy XIV-related functions

The module control remains available when `utility` is disabled, so an administrator can restore it with `m!cog enable utility`.

### Final Fantasy XIV

| Command | Alias | Description | Usage |
| :------ | :---- | :---------- | :---- |
| `m!frontline` | `m!fl` | Shows the current Frontline map and upcoming rotation. | `m!fl` |

### Landmines

Based on a funny bit from [Max0r's server](https://x.com/realMax0r/status/1982196340387188780). When enabled, landmines can drop with a 1% chance every time a message is sent, and another 1% chance to detonate it to time them out for 30 seconds (up to 3 minutes).

To avoid being too annoying, the module must be **enabled per channel** by a server admin.

|Command|Description|Usage|
|---|---|---|
|`y!lm allow`|Enables landmines in the current channel.|`y!lm allow`|
|`y!lm restrict`|Disables landmines and clears all active mines.|`y!lm restrict`|
|`y!lm config`|View or change per‑channel settings.|`y!lm config [setting] [value]`|
|`y!lm clear`|Clear all active mines from the current channel.|`y!lm clear`|
|`y!lm check`|Shows the number of active mines in the channel.|`y!lm check`|
|`y!lm drop [1-10]`|Manually places at a 10s cooldown).|`y!lm drop 5`|
|`y!lm step`|Manually triggers a mine (5s cooldown).|`y!lm step`|
|`y!lm stats [@user]`|Displays landmine statistics for a user.|`y!lm stats @ajisai_ame`|
|`y!lm serverstats`|Shows server‑wide landmine statistics.|`y!lm serverstats`|
|`y!lm top`|Global leaderboards of landmine statistics.|`y!lm top`|
|`y!lm rateup`|Checks if the trigger rate‑up is currently active.|`y!lm rateup`|
