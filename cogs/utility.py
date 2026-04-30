import asyncio
import logging
import random
import re
from typing import Optional

import discord
from discord.ext import commands
from discord.utils import format_dt

from config import EMBED_COLORS, EMOJIS

logger = logging.getLogger("Yamashiro.Utility")


class Utility(commands.Cog):
    """Essential services and general assistance, Milord!"""

    def __init__(self, bot):
        self.bot = bot

    def create_embed(
        self, title: str, description: str, color_key="utility", fields=None
    ) -> discord.Embed:
        """Centralized helper for consistent embed styling."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=EMBED_COLORS.get(color_key, 0x2F3136),
            timestamp=discord.utils.utcnow(),
        )
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
        return embed

    def parse_relative_time(self, time_input: str) -> Optional[int]:
        """Convert strings like 10m or 1h into seconds."""
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        match = re.match(r"(\d+)([smhd])", time_input.lower())
        if match:
            return int(match.group(1)) * units[match.group(2)]
        return None

    # --- Listeners ---
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Adds a visual cue when a command is acknowledged."""
        if ctx.command and ctx.command.cog_name == "Landmine":
            return
        try:
            await ctx.message.add_reaction("🏮")
        except (discord.Forbidden, discord.HTTPException):
            pass

    # --- Commands ---
    @commands.command(name="help", aliases=["commands", "h"])
    async def help_command(self, ctx):
        """Displays the main command directory."""
        embed = self.create_embed(
            title=f"{EMOJIS.get('utility')} Yamashiro at your service!",
            description="*Greetings, Milord. I'll do my very best to assist you!*\n",
            color_key="info",
        )

        embed.add_field(
            name="Utilities",
            value=(
                "`y!serverinfo` - Server overview\n"
                "`y!userinfo [@user]` - Detailed user profile\n"
                "`y!avatar [@user]` - View portrait\n"
                "`y!ping` - Check my speed\n"
                "`y!about` - My status report\n"
            ),
            inline=False,
        )

        embed.add_field(
            name="Fun",
            value=(
                "`y!timer [time] [reason]` - Set a reminder\n"
                "`y!roll [dice]` - Roll dice (e.g., 2d6)\n"
                "`y!flip` - Toss a coin\n"
                "`y!lm help` - Landmine mini-game\n"
            ),
            inline=False,
        )

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}-sama",
            icon_url=ctx.author.display_avatar.url,
        )
        await ctx.send(embed=embed)

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check connection latency."""
        latency = round(self.bot.latency * 1000)
        embed = self.create_embed(
            title="Pong!",
            description=f"*I-I ran as fast as I could, Milord!*\nLatency: **{latency}ms**",
            color_key="success",
        )
        await ctx.send(embed=embed)

    @commands.command(name="about", aliases=["uptime", "status"])
    async def about(self, ctx):
        """Bot status and performance metrics."""
        uptime = discord.utils.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        fields = [
            ("Uptime", f"`{hours}h {minutes}m {seconds}s`", True),
            ("Servers", f"`{len(self.bot.guilds)}`", True),
            ("Latency", f"`{round(self.bot.latency * 1000)}ms`", True),
        ]

        embed = self.create_embed(
            title="Yamashiro Status Report",
            description="*All systems are stable and ready for your orders, Milord!*",
            fields=fields,
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["si"])
    @commands.guild_only()
    async def server_info(self, ctx):
        """Comprehensive server analytics."""
        guild = ctx.guild
        bots = sum(m.bot for m in guild.members)

        boost_count = guild.premium_subscription_count
        boost_level = "None"
        if boost_count >= 14:
            boost_level = "Level 3"
        elif boost_count >= 7:
            boost_level = "Level 2"
        elif boost_count >= 2:
            boost_level = "Level 1"

        fields = [
            ("Owner", guild.owner.mention, True),
            ("Established", format_dt(guild.created_at, "R"), True),
            ("ID", f"`{guild.id}`", True),
            (
                "Members",
                f"👥 {guild.member_count}\n👤 {guild.member_count - bots}\n🤖 {bots}",
                True,
            ),
            (
                "Assets",
                f"Channels: {len(guild.channels)}\nRoles: {len(guild.roles)}",
                True,
            ),
            ("Boosts", f"Level: {boost_level}\nCount: {boost_count}", True),
        ]

        embed = self.create_embed(
            title=f"{guild.name}",
            description=guild.description or "*No description recorded, Milord!*",
            fields=fields,
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["whois", "ui"])
    async def user_info(self, ctx, member: discord.Member = None):
        """Detailed dossiers on server members."""
        member = member or ctx.author

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
            ("Key Permissions", ", ".join(key_perms) if key_perms else "None", False),
        ]

        embed = self.create_embed(
            title=f"{member.display_name}'s Record",
            description=f"{member.mention} | `{member.id}`",
            fields=fields,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.color = (
            member.color
            if member.color != discord.Color.default()
            else EMBED_COLORS["utility"]
        )

        await ctx.send(embed=embed)

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar_command(self, ctx, member: discord.Member = None):
        """View a user's portrait in high resolution."""
        member = member or ctx.author
        embed = self.create_embed(
            title=f"Portrait of {member.display_name}",
            description=f"[**Download Image**]({member.display_avatar.url})",
            color_key="fun",
        )
        embed.set_image(url=member.display_avatar.url)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
