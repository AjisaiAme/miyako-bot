import logging
import re
from typing import Optional

import discord
from discord.ext import commands

from utils.utility_responses import (
    about_embed,
    avatar_embed,
    command_help_embed,
    help_embed,
    module_status_embed,
    module_update_embed,
    unknown_module_embed,
    ping_embed,
    server_info_embed,
    user_info_embed,
)

logger = logging.getLogger("Miyako.Utility")


class Utility(commands.Cog):
    """Essential services and general assistance."""

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

    # listener
    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Adds a reaction to acknowledge commands."""
        if ctx.command and ctx.command.cog_name == "Landmine":
            return
        try:
            await ctx.message.add_reaction("✅")
        except (discord.Forbidden, discord.HTTPException):
            pass

    # main commands
    @commands.command(name="help", aliases=["", "commands", "h"])
    async def help_command(self, ctx, *, section: Optional[str] = None):
        """Main command directory."""
        command = None
        if section:
            parts = section.lower().split()
            command = self.bot.get_command(parts[0])
            for part in parts[1:]:
                if not isinstance(command, commands.Group):
                    command = None
                    break
                command = command.get_command(part)
        if command is not None:
            return await ctx.send(
                embed=command_help_embed(ctx.prefix, ctx.author, command)
            )
        await ctx.send(embed=help_embed(ctx.prefix, ctx.author, section))

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Connection latency check."""
        latency = round(self.bot.latency * 1000)
        await ctx.send(embed=ping_embed(latency))

    @commands.group(name="cog", aliases=["module"], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def module_control(self, ctx):
        """View the server's cog status."""
        lines = []
        for key, cog_name in self.bot.managed_cogs.items():
            status = "enabled" if await self.bot.is_cog_enabled(ctx.guild.id, cog_name) else "disabled"
            lines.append(f"**{key}**: {status}")
        await ctx.send(embed=module_status_embed(lines))

    @module_control.command(name="enable")
    async def enable_cog(self, ctx, cog_name: str):
        """Enable a cog for this server."""
        normalized = cog_name.lower()
        if normalized not in self.bot.managed_cogs:
            return await ctx.send(embed=unknown_module_embed(cog_name))
        await self.bot.set_cog_enabled(
            ctx.guild.id, self.bot.managed_cogs[normalized], True
        )
        await ctx.send(embed=module_update_embed(normalized, True))

    @module_control.command(name="disable")
    async def disable_cog(self, ctx, cog_name: str):
        """Disable a cog for this server."""
        normalized = cog_name.lower()
        if normalized not in self.bot.managed_cogs:
            return await ctx.send(embed=unknown_module_embed(cog_name))
        await self.bot.set_cog_enabled(
            ctx.guild.id, self.bot.managed_cogs[normalized], False
        )
        await ctx.send(embed=module_update_embed(normalized, False))

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
    async def user_info(self, ctx, member: Optional[discord.Member] = None):
        """Member dossier."""
        member = member or ctx.author
        await ctx.send(embed=user_info_embed(member))

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar_command(self, ctx, member: Optional[discord.Member] = None):
        """High‑resolution portrait."""
        member = member or ctx.author
        await ctx.send(embed=avatar_embed(member))


async def setup(bot):
    await bot.add_cog(Utility(bot))
