import discord
from discord.utils import format_dt

from .helpers import create_embed


def help_embed(prefix: str, invoker: discord.Member) -> discord.Embed:
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
        ),
        inline=False,
    )
    embed.add_field(
        name="Fun",
        value=(
            f"`{prefix}roll [dice]` – Roll dice with modifiers\n"
            f"`{prefix}poll <string> <option1> <option2>` – Start a button poll\n"
            f"`{prefix}timer [minutes] [label]` – Set a countdown timer\n"
            f"`{prefix}choose item1, item2` – Pick one option\n"
            f"`{prefix}flip [heads/tails]` – Toss a coin\n"
            f"`{prefix}random [min] [max]` – Get a random integer\n"
            f"`{prefix}rate <thing>` – Rate something from 1–10\n"
            f"`{prefix}lm help` – Landmine mini-game\n"
            f"`{prefix}frontline` – View the Frontline rotation\n"
        ),
        inline=False,
    )
    embed.set_footer(
        text=f"Requested by {invoker.display_name}",
        icon_url=invoker.display_avatar.url,
    )
    return embed


# ping
def ping_embed(latency_ms: int) -> discord.Embed:
    return create_embed(
        title="Latency",
        description=f"**{latency_ms}ms**",
        colour_key="success",
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
        title="Bot Status",
        description="The bot is operational.",
        fields=fields,
        colour_key="utility",
    )
    embed.set_thumbnail(url=avatar_url)
    return embed


# --------------------------------------------------------------------------
# Server Info
# --------------------------------------------------------------------------
def server_info_embed(guild: discord.Guild) -> discord.Embed:
    bots = sum(m.bot for m in guild.members)
    humans = guild.member_count - bots

    boost_count = guild.premium_subscription_count
    if boost_count >= 14:
        boost_level = "Level 3"
    elif boost_count >= 7:
        boost_level = "Level 2"
    elif boost_count >= 2:
        boost_level = "Level 1"
    else:
        boost_level = "None"

    fields = [
        ("Owner", guild.owner.mention, True),
        ("Established", format_dt(guild.created_at, "R"), True),
        ("ID", f"`{guild.id}`", True),
        (
            "Members",
            f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}",
            True,
        ),
        ("Assets", f"Channels: {len(guild.channels)}\nRoles: {len(guild.roles)}", True),
        ("Boosts", f"Level: {boost_level}\nCount: {boost_count}", True),
    ]

    embed = create_embed(
        title=guild.name,
        description=guild.description or "No description recorded.",
        fields=fields,
        colour_key="utility",
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
        colour_key="utility",
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
