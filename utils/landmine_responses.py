import discord
from typing import Optional

from .helpers import create_embed


def help_embed(
    prefix: str, now_str: Optional[str] = None, in_rateup: Optional[bool] = None
) -> discord.Embed:
    desc = (
        "*Watch your step. Your messages may trigger hidden explosives.*\n\n"
        f"Use `{prefix}lm allow` to enable the game in this channel."
    )
    if now_str is not None and in_rateup is not None:
        desc += (
            f"\n\n**Rate-Up:** {'Active' if in_rateup else 'Inactive'} "
            f"at {now_str} (Asia/Singapore)."
        )
    embed = create_embed("Landmine", desc, colour_key="landmine")

    admin_cmds = (
        f"`{prefix}lm allow` – Enable the module in this channel\n"
        f"`{prefix}lm restrict` – Disable and and clear all mines from current channel\n"
        f"`{prefix}lm config` – Adjust drop/trigger chances & timeout length\n"
        f"`{prefix}lm clear` – Delete all active mines\n"
        f"`{prefix}lm wl` – List all whitelisted in the server"
    )
    embed.add_field(name="Admin Commands", value=admin_cmds, inline=False)

    user_cmds = (
        f"`{prefix}lm drop [1-10]` – Manually place mines (10s cooldown)\n"
        f"`{prefix}lm check` – See how many mines are active\n"
        f"`{prefix}lm stats [@user]` – View user stats\n"
        f"`{prefix}lm serverstats` – View server‑wide stats\n"
        f"`{prefix}lm top` – View global leaderboard\n"
        f"`{prefix}lm rateup` – Check for rate‑up times\n"
        f"`{prefix}lm step` – Probably best to avoid this one\n"
    )
    embed.add_field(name="Player Commands", value=user_cmds, inline=False)
    return embed


def channel_status_field(prefix: str) -> tuple:
    return (
        "Channel Status",
        f"This channel is **not enabled** for landmines.\nUse `{prefix}lm allow` to activate.",
        False,
    )


def current_config_field(
    channel_name: str,
    config: dict,
    active_mines: int,
    effective_trigger_chance: Optional[int] = None,
) -> tuple:
    trigger_chance = (
        effective_trigger_chance
        if effective_trigger_chance is not None
        else config["trigger_chance"]
    )
    trigger_note = ""
    if (
        effective_trigger_chance is not None
        and effective_trigger_chance != config["trigger_chance"]
    ):
        trigger_note = " *(rate-up active)*"

    config_text = (
        f"**Landmine Odds:** `1 in {config['landmine_chance']}` messages\n"
        f"**Trigger Odds:** `1 in {trigger_chance}` messages{trigger_note}\n"
        f"**Timeout Duration:** `{config['timeout_duration']} seconds`\n"
        f"**Active Mines:** {active_mines}"
    )
    return f"Current Settings for `#{channel_name}`", config_text, False


def already_enabled(channel_mention: str) -> discord.Embed:
    return create_embed(
        "Already Enabled!",
        f"Landmines are already active in {channel_mention}.",
        colour_key="info",
    )


def landmines_enabled(channel_mention: str) -> discord.Embed:
    return create_embed(
        "Landmines Enabled!",
        f"Landmines are now active in {channel_mention}. Be careful!",
        colour_key="success",
    )


def already_restricted(channel_mention: str) -> discord.Embed:
    return create_embed(
        "Already Restricted!",
        f"Landmines are already disabled in {channel_mention}.",
        colour_key="info",
    )


def landmines_restricted(channel_mention: str) -> discord.Embed:
    return create_embed(
        "Landmines Restricted!",
        f"Landmines have been cleared from {channel_mention}. The channel is now safe.",
        colour_key="warning",
    )


def not_enabled() -> discord.Embed:
    return create_embed(
        "Not Enabled!",
        "Landmines are not active in this channel.",
        colour_key="warning",
    )


def mines_cleared(channel_mention: str) -> discord.Embed:
    return create_embed(
        "Mines Cleared",
        f"All active landmines have been removed from {channel_mention}.",
        colour_key="success",
    )


def no_danger() -> discord.Embed:
    return create_embed(
        "No danger in sight!",
        "The path is clear. Walk freely!",
        colour_key="info",
    )


def boom_embed(member: discord.Member, timeout: int, remaining: int) -> discord.Embed:
    desc = (
        f"{member.mention} stepped on a landmine! "
        f"They're timed out for **{timeout} seconds**\n\n"
        f"**{remaining}** landmine(s) remain"
    )
    return create_embed("💥 BOOM!", desc, colour_key="landmine")



def mine_placed(member: discord.abc.User, count: int) -> discord.Embed:
    return create_embed(
        "Watch your step!",
        f"{member.mention} just dropped {count} mine(s).",
        colour_key="landmine",
    )


def member_not_found() -> discord.Embed:
    return create_embed("Error", "Could not find member.", colour_key="warning")


def too_powerful(member: discord.Member) -> discord.Embed:
    return create_embed(
        "That mine had no effect.",
        f"{member.mention} stepped on a mine, but they're too powerful!",
        colour_key="warning",
    )


def missing_permissions() -> discord.Embed:
    return create_embed(
        "Permission Error",
        "I lack the `Moderate Members` permission to apply timeouts.",
        colour_key="error",
    )


def forbidden_timeout() -> discord.Embed:
    return create_embed(
        "Permission Denied",
        "Sorry, I am not allowed to time out this member.",
        colour_key="error",
    )


def unexpected_error() -> discord.Embed:
    return create_embed(
        "Error",
        "An unexpected error occurred while applying the timeout.",
        colour_key="error",
    )

def config_view(prefix: str, channel_mention: str, config: dict) -> discord.Embed:
    fields = [
        (
            "`landmine_chance`",
            f"`1 in {config['landmine_chance']}` messages\n"
            "*Chance for any message to automatically drop a mine.*",
            False,
        ),
        (
            "`trigger_chance`",
            f"`1 in {config['trigger_chance']}` messages\n"
            "*Chance to step on a mine when one is present.*",
            False,
        ),
        (
            "`timeout_duration`",
            f"**Current:** `{config['timeout_duration']}` seconds\n"
            "*How long the user is timed out after triggering a mine.*\n"
            "Can be set to a maximum of `180` seconds (3 minutes).",
            False,
        ),
    ]
    embed = create_embed(
        "Landmine Configuration",
        f"Settings for {channel_mention}\n"
        f"Use `{prefix}lm config <setting> <value>` to modify.",
    )
    for name, value, inline in fields:
        embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text="Admin only • Changes apply immediately")
    return embed


def config_updated(setting: str, value: int) -> discord.Embed:
    return create_embed(
        "Configuration Updated!",
        f"`{setting}` has been set to `{value}`.",
        colour_key="success",
    )


def invalid_setting(valid: tuple) -> discord.Embed:
    return create_embed(
        "Invalid setting",
        f"Choose from: {', '.join(valid)}",
        colour_key="error",
    )


def missing_value(setting: str, prefix: str) -> discord.Embed:
    return create_embed(
        "Missing value",
        f"Provide a new value for `{setting}`.\n"
        f"Example: `{prefix}lm config {setting} 200`",
        colour_key="error",
    )


def value_at_least_one(setting: str) -> discord.Embed:
    return create_embed(
        "Invalid value",
        f"`{setting}` must be at least 1.",
        colour_key="error",
    )


def timeout_minimum() -> discord.Embed:
    return create_embed(
        "Invalid timeout",
        "Timeout duration must be at least 1 second.",
        colour_key="error",
    )


def timeout_maximum() -> discord.Embed:
    return create_embed(
        "Invalid timeout",
        "Timeout duration cannot exceed 180 seconds (3 minutes).",
        colour_key="error",
    )


# stats
def user_stats(
    member: discord.Member, guild_name: str, sent: int, trig: int, placed: int
) -> discord.Embed:
    embed = create_embed(
        f"Landmine Stats of `{member.display_name}`",
        f"Activity in `{guild_name}`",
    )
    embed.add_field(name="Messages Sent", value=f"`{sent}`", inline=True)
    embed.add_field(name="Times Triggered", value=f"`{trig}`", inline=True)
    embed.add_field(name="Mines Placed", value=f"`{placed}`", inline=True)
    return embed


def global_top(rows: list) -> discord.Embed:
    lines = []
    for i, (user, trig) in enumerate(rows, 1):
        lines.append(f"{i}. **{user}** — {trig}")
    return create_embed("Top Victims", "\n".join(lines))


def server_stats(
    total_sent: int,
    total_triggered: int,
    total_placed: int,
    top_users: list,
    guild_name: str,
    icon_url: Optional[str] = None,
) -> discord.Embed:
    embed = create_embed(f"Landmine Stats for `{guild_name}`", "")
    embed.add_field(name="Total Messages Sent", value=f"`{total_sent}`", inline=True)
    embed.add_field(
        name="Total Mines Triggered", value=f"`{total_triggered}`", inline=True
    )
    embed.add_field(name="Total Mines Placed", value=f"`{total_placed}`", inline=True)
    if top_users:
        embed.add_field(name="Top Victims", value="\n".join(top_users), inline=False)
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    return embed


# rate-up
def rateup(now_str: str, in_rateup: bool) -> discord.Embed:
    desc = f"Current time: {now_str} (Asia/Singapore)\n"
    if in_rateup:
        desc += "**Rate‑Up Active!**"
    else:
        desc += "Rate‑up is not active."
    embed = create_embed(
        "Landmine Rate‑Up", desc, colour_key="landmine" if in_rateup else "info"
    )
    embed.add_field(name="Rate‑Up Hours", value="0:00 – 3:00", inline=True)
    embed.add_field(name="Multiplier", value="1/5 of base chance", inline=True)
    return embed


# whitelists
def whitelisted_channels(channels: list) -> discord.Embed:
    if not channels:
        return create_embed(
            "No Active Channels",
            "No channel has landmines enabled in this server.",
            colour_key="info",
        )

    lines = "\n".join(
        f"{ch.mention if hasattr(ch, 'mention') else ch}" for ch in channels
    )

    return create_embed("Whitelisted Channels", lines)
