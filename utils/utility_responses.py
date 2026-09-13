import discord
from discord.utils import format_dt
from discord.ext import commands
from typing import Optional

from .helpers import create_embed


# --------------------------------------------------------------------------
# Main Help
# --------------------------------------------------------------------------
def help_embed(
    prefix: str, invoker: discord.Member, section: Optional[str] = None
) -> discord.Embed:
    embed = create_embed(
        title="Miyako",
        description="Available commands and server utilities.\n",
        colour_key="info",
    )
    embed.add_field(
        name="Utilities",
        value=(
            f"`{prefix}serverinfo` – Server overview\n"
            f"`{prefix}userinfo [@user]` – Detailed user profile\n"
            f"`{prefix}avatar [@user]` – View portrait\n"
            f"`{prefix}ping` – Check latency\n"
            f"`{prefix}about` – View bot status\n"
            f"`{prefix}cog` (`{prefix}module`) – View or manage Miyako's modules\n"
        ),

        ),
        "fun": (
            f"`{prefix}roll [dice]` – Roll dice with modifiers\n"
            f"`{prefix}poll <string> <option1> <option2>` – Start a button poll\n"
            f"`{prefix}timer [minutes] [label]` – Set a countdown timer\n"
            f"`{prefix}choose item1, item2` – Pick one option\n"
            f"`{prefix}flip [heads/tails]` – Toss a coin\n"
            f"`{prefix}random [min] [max]` – Get a random integer\n"
            f"`{prefix}rate <thing>` – Rate something from 1–10\n"
        ),
        "fun": (
            f"`{prefix}roll [dice]` – Roll dice with modifiers\n"
            f"`{prefix}flip [heads/tails]` – Toss a coin\n"
            f"`{prefix}random [min] [max]` – Get a random integer\n"
            f"`{prefix}rate <thing>` – Rate something from 1–10\n"
            f"`{prefix}lm help` – Landmine mini-game\n"
            f"`{prefix}frontline` – View the Frontline rotation\n"
        ),

        ),
        "xiv": (
            f"`{prefix}frontline` (`{prefix}fl`) – Show the current Frontline map and rotation\n"
        ),
        "landmine": (
            f"`{prefix}landmine` (`{prefix}lm`) – Open the landmine menu\n"
            f"`{prefix}lm allow` – Enable landmines in this channel\n"
            f"`{prefix}lm restrict` – Disable landmines and clear active mines\n"
            f"`{prefix}lm config [setting] [value]` – View or update settings\n"
            f"`{prefix}lm clear` – Remove all active mines\n"
            f"`{prefix}lm drop [1-10]` – Place mines manually\n"
            f"`{prefix}lm step` – Trigger a mine yourself\n"
            f"`{prefix}lm check` – Show active mines in this channel\n"
            f"`{prefix}lm stats [@user]` – View landmine statistics\n"
            f"`{prefix}lm serverstats` (`{prefix}lm ss`, `{prefix}lm guildstats`) – View server statistics\n"
            f"`{prefix}lm top` – View the global leaderboard\n"
            f"`{prefix}lm rateup` – Check the current rate-up status\n"
            f"`{prefix}lm wl` (`{prefix}lm list`, `{prefix}lm whitelist`) – List enabled channels\n"
        ),
    }
    section_aliases = {"utility": "utilities", "utils": "utilities", "final fantasy xiv": "xiv", "lm": "landmine"}
    selected_section = section_aliases.get(section.lower(), section.lower()) if section else None
    if selected_section not in sections:
        selected_section = None

    for name, value in sections.items():
        if selected_section is None or selected_section == name:
            display_name = "Final Fantasy XIV" if name == "xiv" else name.title()
            embed.add_field(name=display_name, value=value, inline=False)
    embed.set_footer(
        text=f"Requested by {invoker.display_name}",
        icon_url=invoker.display_avatar.url,
    )
    return embed


def command_help_embed(
    prefix: str, invoker: discord.Member, command: commands.Command
) -> discord.Embed:
    aliases = ", ".join(f"`{prefix}{alias}`" for alias in command.aliases)
    usage = command.usage or command.signature
    description = command.help or command.description or "No description available."

    embed = create_embed(
        title=f"{prefix}{command.name}",
        description=description,
        colour_key="default",
    )
    if usage:
        embed.add_field(
            name="Usage", value=f"`{prefix}{command.name} {usage}`", inline=False
        )
    if aliases:
        embed.add_field(name="Aliases", value=aliases, inline=False)
    embed.set_footer(
        text=f"Requested by {invoker.display_name}",
        icon_url=invoker.display_avatar.url,
    )
    return embed


def module_status_embed(status_lines: list[str]) -> discord.Embed:
    return create_embed(
        "Server Modules", "\n".join(status_lines), colour_key="default"
    )


def module_update_embed(module: str, enabled: bool) -> discord.Embed:
    action = "Enabled" if enabled else "Disabled"
    return create_embed(
        f"Module {action}",
        f"`{module}` is now {action.lower()} for this server.",
        colour_key="default",
    )


def unknown_module_embed(module: str) -> discord.Embed:
    return create_embed(
        "Unknown Module",
        f"`{module}` is not a managed module.",
        colour_key="default",
    )


def module_disabled_embed(module: str, prefix: str) -> discord.Embed:
    return create_embed(
        "Module Disabled",
        f"The `{module}` module is disabled in this server.\n"
        f"An admin can enable it with `{prefix}cog enable {module}`.",
        colour_key="default",
    )


def module_permission_embed(prefix: str) -> discord.Embed:
    return create_embed(
        "Permission Required",
        "Only members with the `Manage Server` permission can change Miyako's modules.\n"
        f"Use `{prefix}cog` to view the current module status.",
        colour_key="default",
    )


# ping
def ping_embed(latency_ms: int) -> discord.Embed:
    return create_embed(
        title="Pong!",
        description=f"*That was quick.*\nLatency: **{latency_ms}ms**",
        colour_key="default",
    )
    )


def about_embed(
    uptime_str: str,
    guild_count: int,
    latency_ms: int,
    avatar_url: str,
) -> discord.Embed:
    fields = [
        ("Uptime", f"`{uptime_str}`", True),
        ("Servers", f"`{guild_count}`", True),
        ("Latency", f"`{latency_ms}ms`", True),
    ]
    embed = create_embed(
        title="About Miyako",
        description="*All systems are stable!*",

        fields=fields,
        colour_key="default",
    )
    embed.set_thumbnail(url=avatar_url)
    return embed


# --------------------------------------------------------------------------
# Server Info
# --------------------------------------------------------------------------
def server_info_embed(guild: discord.Guild) -> discord.Embed:
    bots = sum(m.bot for m in guild.members)
    total_members = guild.member_count or 0
    humans = total_members - bots


    boost_count = guild.premium_subscription_count or 0
    owner = guild.owner
    owner_mention = owner.mention if owner else "Unknown"
    if boost_count >= 14:
        boost_level = "Level 3"
    elif boost_count >= 7:
        boost_level = "Level 2"
    elif boost_count >= 2:
        boost_level = "Level 1"
    else:
        boost_level = "None"

    fields = [
        ("Owner", guild.owner.mention if guild.owner else "Unknown", True),

        ("Established", format_dt(guild.created_at, "R"), True),
        ("ID", f"`{guild.id}`", True),
        (
            "Members",
            f"Total: {total_members}\nHumans: {humans}\nBots: {bots}",
            True,
        ),
        ("Assets", f"Channels: {len(guild.channels)}\nRoles: {len(guild.roles)}", True),
        ("Boosts", f"Level: {boost_level}\nCount: {boost_count}", True),
    ]

    embed = create_embed(
        title=guild.name,
        description=guild.description or "*No description recorded.*",

        fields=fields,
        colour_key="default",
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    return embed


# --------------------------------------------------------------------------
# User Info
# --------------------------------------------------------------------------
def user_info_embed(member: discord.Member) -> discord.Embed:
    key_perms = [
        p[0].replace("_", " ").title()
        for p in member.guild_permissions
        if p[1]
        and p[0]
        in (
            "administrator",
            "manage_guild",
            "manage_roles",
            "kick_members",
            "ban_members",
        )
    ]

    fields = [
        ("Account Created", format_dt(member.created_at, "R"), True),
        (
            "Joined Server",
            format_dt(member.joined_at, "R") if member.joined_at else "Unknown",
            True,
        ),
        (
            "Top Role",
            member.top_role.mention if len(member.roles) > 1 else "None",
            False,
        ),
        (
            "Key Permissions",
            ", ".join(key_perms) if key_perms else "None",
            False,
        ),
    ]

    embed = create_embed(
        title=f"{member.display_name}'s Profile",
        description=f"{member.mention} | `{member.id}`",
        fields=fields,
        colour_key="default",
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    if member.colour != discord.Color.default():
        embed.colour = member.colour
    return embed


# --------------------------------------------------------------------------
# Avatar
# --------------------------------------------------------------------------
def avatar_embed(member: discord.Member) -> discord.Embed:
    embed = create_embed(
        title=f"Avatar: {member.display_name}",
        description=f"[**Download Image**]({member.display_avatar.url})",
        colour_key="fun",
    )
    embed.set_image(url=member.display_avatar.url)
    return embed
