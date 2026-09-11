import logging
import re
from typing import Optional

import discord
from discord.ext import commands

from utils.utility_responses import (
    about_embed,
    avatar_embed,
    help_embed,
    ping_embed,
    server_info_embed,
    user_info_embed,
)

logger = logging.getLogger("Yamashiro.Utility")


class Utility(commands.Cog):
    """Essential services and general assistance, Milord!"""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def parse_relative_time(time_input: str) -> Optional[int]:
        """Convert strings like 10m or 1h into seconds."""
        units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
        match = re.match(r"(\d+)([smhd])", time_input.lower())
        if match:
            return int(match.group(1)) * units[match.group(2)]
        return None

    # --- Listener (visual cue, left as‑is because it’s not a message) ---
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Adds a lantern reaction to acknowledge commands."""
        if ctx.command and ctx.command.cog_name == "Landmine":
            return
        try:
            await ctx.message.add_reaction("🏮")
        except (discord.Forbidden, discord.HTTPException):
            pass

    # --- Commands ---
    @commands.command(name="help", aliases=["", "commands", "h"])
    async def help_command(self, ctx):
        """Main command directory."""
        await ctx.send(embed=help_embed(ctx.prefix, ctx.author))

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Connection latency check."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(embed=ping_embed(latency))

    @commands.command(name="about", aliases=["uptime", "status"])
    async def about(self, ctx):
        """Bot performance metrics."""
        uptime = discord.utils.utcnow() - self.bot.start_time
        hours, rem = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        await ctx.send(
            embed=about_embed(
                uptime_str,
                len(self.bot.guilds),
                round(self.bot.latency * 1000),
                self.bot.user.display_avatar.url,
            )
        )

    @commands.command(name="serverinfo", aliases=["si"])
    @commands.guild_only()
    async def server_info(self, ctx):
        """Server analytics."""
        await ctx.send(embed=server_info_embed(ctx.guild))

    @commands.command(name="userinfo", aliases=["whois", "ui"])
    async def user_info(self, ctx, member: discord.Member = None):
        """Member dossier."""
        member = member or ctx.author
        await ctx.send(embed=user_info_embed(member))

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar_command(self, ctx, member: discord.Member = None):
        """High‑resolution portrait."""
        member = member or ctx.author
        await ctx.send(embed=avatar_embed(member))


async def setup(bot):
    await bot.add_cog(Utility(bot))
