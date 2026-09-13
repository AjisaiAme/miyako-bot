import discord
from typing import Optional

from .helpers import create_embed


def help_embed(
    prefix: str, now_str: Optional[str] = None, in_rateup: Optional[bool] = None
) -> discord.Embed:
    desc = (
        "*Watch your step.* Messages may trigger landmines.\n\n"
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
        f"`{prefix}lm restrict` – Disable and clear all mines from the current channel\n"
        f"`{prefix}lm config` – Adjust drop/trigger chances & timeout length\n"
        f"`{prefix}lm clear` – Delete all active mines\n"
        f"`{prefix}lm wl` – List all whitelisted channels in the server"
    )
    embed.add_field(name="Admin Commands", value=admin_cmds, inline=False)

    user_cmds = (
        f"`{prefix}lm drop [1-10]` – Manually place mines (10s cooldown)\n"
        f"`{prefix}lm check` – See how many mines are active\n"
        f"`{prefix}lm stats [@user]` – View user stats\n"
        f"`{prefix}lm serverstats` – View server-wide stats\n"
        f"`{prefix}lm top` – View the global leaderboard\n"
        f"`{prefix}lm rateup` – Check for rate-up times\n"
        f"`{prefix}lm step` – Trigger a mine manually (best avoided)"
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
        "No Active Mines",
        "The path is clear. Walk freely!",
        colour_key="info",
    )


def boom_embed(member: discord.Member, timeout: int, remaining: int) -> discord.Embed:
    desc = (
        f"{member.mention} stepped on a landmine! "
        f"They're timed out for **{timeout} seconds**\n\n"
        f"**{remaining}** landmine(s) remain"
    )
    return create_embed("Landmine Triggered", desc, colour_key="landmine")


def mine_placed(member: discord.abc.User, count: int) -> discord.Embed:
    return create_embed(
        "Uh-oh!",
        f"{member.mention} just dropped {count} mine(s).",
        colour_key="landmine",
    )


def member_not_found() -> discord.Embed:
    return create_embed("Error", "Could not find member.", colour_key="warning")


def too_powerful(member: discord.Member) -> discord.Embed:
    return create_embed(
        "... Eh?",
        f"{member.mention} stepped on a mine, but they're too powerful to be timed out.",
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


def config_view(
    prefix: str,
    channel_mention: str,
    config: dict,
    effective_trigger_chance: Optional[int] = None,
) -> discord.Embed:
    trigger_text = f"`1 in {config['trigger_chance']}` messages"
    if (
        effective_trigger_chance is not None
        and effective_trigger_chance != config["trigger_chance"]
    ):
        trigger_text = (
            f"Base: `1 in {config['trigger_chance']}` messages\n"
            f"Rate-up: `1 in {effective_trigger_chance}` messages"
        )

    fields = [
        (
            "`landmine_chance`",
            f"`1 in {config['landmine_chance']}` messages\n"
            "*Chance for any message to automatically drop a mine.*",
            False,
        ),
        (
            "`trigger_chance`",
            f"{trigger_text}\n"
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
        (
            "`rateup`",
            f"**Status:** `{'enabled' if config.get('rateup_enabled', True) else 'disabled'}`\n"
            f"**Window:** `{config.get('rateup_start_hour', 0):02d}:00 - "
            f"{config.get('rateup_end_hour', 3):02d}:00`\n"
            f"**Multiplier:** `1/{config.get('rateup_multiplier', 5)}`\n"
            "*Use `lm rateup` to update these settings.*",
            False,
        ),
    ]

    embed = create_embed(
        "Landmine Configuration",
        f"Settings for {channel_mention}\n"
        f"Use `{prefix}lm config <setting> <value>` to modify.",
        colour_key="landmine",
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
        colour_key="landmine",
    )
    embed.add_field(name="Messages Sent", value=f"`{sent}`", inline=True)
    embed.add_field(name="Times Triggered", value=f"`{trig}`", inline=True)
    embed.add_field(name="Mines Placed", value=f"`{placed}`", inline=True)
    return embed


def global_top(rows: list) -> discord.Embed:
    lines = []
    for i, (user, trig) in enumerate(rows, 1):
        lines.append(f"{i}. **{user}** — {trig}")
    return create_embed("Top Trigger Counts", "\n".join(lines), colour_key="landmine")


def server_stats(
    total_sent: int,
    total_triggered: int,
    total_placed: int,
    top_users: list,
    guild_name: str,
    icon_url: Optional[str] = None,
) -> discord.Embed:
    embed = create_embed(
        f"Landmine Stats for `{guild_name}`",
        "",
        colour_key="landmine",
    )
    embed.add_field(name="Total Messages Sent", value=f"`{total_sent}`", inline=True)
    embed.add_field(
        name="Total Mines Triggered", value=f"`{total_triggered}`", inline=True
    )
    embed.add_field(name="Total Mines Placed", value=f"`{total_placed}`", inline=True)
    if top_users:
        embed.add_field(
            name="Top Trigger Counts",
            value="\n".join(top_users),
            inline=False,
        )
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    return embed


# rate-up

def rateup(
    now_str: str,
    in_rateup: bool,
    enabled: bool,
    start_hour: int,
    end_hour: int,
    multiplier: int,
    base_trigger_chance: int,
    effective_trigger_chance: int,
    prefix: str,
) -> discord.Embed:
    desc = f"Current time: `{now_str}` (Asia/Singapore)\n"
    if not enabled:
        status = "Disabled"
        colour = "info"
    elif in_rateup:
        status = "Active"
        colour = "landmine"
    else:
        status = "Scheduled"
        colour = "info"

    embed = create_embed("Landmine Rate-Up", desc, colour_key=colour)
    embed.add_field(name="Status", value=f"**{status}**", inline=True)
    embed.add_field(
        name="Schedule",
        value=f"`{start_hour:02d}:00 – {end_hour:02d}:00`",
        inline=True,
    )
    embed.add_field(
        name="Trigger Odds",
        value=(
            f"Base: `1 in {base_trigger_chance}`\n"
            f"Current: `1 in {effective_trigger_chance}`"
        ),
        inline=True,
    )
    embed.add_field(
        name="Multiplier",
        value=f"`1/{multiplier}` while active",
        inline=True,
    )
    embed.add_field(
        name="Admin Controls",
        value=(
            f"`{prefix}lm rateup enable` / `disable`\n"
            f"`{prefix}lm rateup hours {start_hour} {end_hour}`\n"
            f"`{prefix}lm rateup multiplier {multiplier}`"
        ),
        inline=False,
    )
    embed.set_footer(text="Rate-up settings apply to this channel.")
    return embed


def rateup_invalid(message: str) -> discord.Embed:
    return create_embed("Invalid Rate-Up Setting", message, colour_key="error")


def rateup_updated(config) -> discord.Embed:
    status = "enabled" if config.rateup_enabled else "disabled"
    return create_embed(
        "Rate-Up Updated",
        f"Rate-up is now **{status}**.\n"
        f"Window: `{config.rateup_start_hour:02d}:00 - {config.rateup_end_hour:02d}:00`\n"
        f"Multiplier: `1/{config.rateup_multiplier}` of base chance.",
        colour_key="success",
    )


# whitelists

def whitelisted_channels(channels: list) -> discord.Embed:
    if not channels:
        return create_embed(
            "No Active Channels",
            "No channel has landmines enabled in this server.",
            colour_key="landmine",
        )

    lines = "\n".join(
        f"{ch.mention if hasattr(ch, 'mention') else ch}" for ch in channels
    )
    return create_embed("Whitelisted Channels", lines, colour_key="landmine")
