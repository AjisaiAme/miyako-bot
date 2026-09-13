import asyncio
import logging
import random
from pathlib import Path

import aiosqlite
import discord
from discord.ext import commands

from config import BOT_TOKEN, PREFIX
from utils.utility_responses import (
    module_disabled_embed,
    module_permission_embed,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("Miyako")
DB_PATH = str(Path(__file__).resolve().parent / "miyako_data.db")
MANAGED_COGS = {
    "utility": "Utility",
    "fun": "Fun",
    "landmine": "Landmine",
    "xiv": "XIV",
}


class MiyakoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        self.start_time = discord.utils.utcnow()
        self.managed_cogs = MANAGED_COGS
        self._disabled_cogs: dict[int, set[str]] = {}
        # cog modules
        self.initial_extensions = [
            "cogs.fun",
            "cogs.utility",
            "cogs.landmine",
            "cogs.xiv",
        ]

    async def setup_hook(self):
        logger.info("Initializing...")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS disabled_cogs (
                    guild_id INTEGER NOT NULL,
                    cog_name TEXT NOT NULL,
                    PRIMARY KEY (guild_id, cog_name)
                )
                """
            )
            await db.commit()

        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded: {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

        self.add_check(self._check_cog_enabled)

    async def _check_cog_enabled(self, ctx: commands.Context) -> bool:
        if ctx.guild is None or ctx.command is None:
            return True

        if ctx.command.qualified_name.split()[0] == "cog":
            return True

        cog_name = ctx.command.cog_name
        if cog_name is None or cog_name not in MANAGED_COGS.values():
            return True

        return await self.is_cog_enabled(ctx.guild.id, cog_name)

    async def is_cog_enabled(self, guild_id: int, cog_name: str) -> bool:
        if guild_id not in self._disabled_cogs:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    "SELECT cog_name FROM disabled_cogs WHERE guild_id = ?",
                    (guild_id,),
                ) as cursor:
                    rows = await cursor.fetchall()
            self._disabled_cogs[guild_id] = {row[0] for row in rows}
        return cog_name not in self._disabled_cogs[guild_id]

    async def set_cog_enabled(
        self, guild_id: int, cog_name: str, enabled: bool
    ) -> None:
        async with aiosqlite.connect(DB_PATH) as db:
            if enabled:
                await db.execute(
                    "DELETE FROM disabled_cogs WHERE guild_id = ? AND cog_name = ?",
                    (guild_id, cog_name),
                )
            else:
                await db.execute(
                    "INSERT OR IGNORE INTO disabled_cogs (guild_id, cog_name) VALUES (?, ?)",
                    (guild_id, cog_name),
                )
            await db.commit()

        disabled = self._disabled_cogs.setdefault(guild_id, set())
        if enabled:
            disabled.discard(cog_name)
        else:
            disabled.add(cog_name)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            command = ctx.command
            if command and command.qualified_name.split()[0] == "cog":
                await ctx.send(
                    embed=module_permission_embed(ctx.prefix or PREFIX)
                )
                return

        if isinstance(error, commands.CheckFailure):
            command = ctx.command
            cog_name = command.cog_name if command else None
            if ctx.guild is None or cog_name is None:
                return
            if cog_name not in MANAGED_COGS.values():
                return
            if not await self.is_cog_enabled(ctx.guild.id, cog_name):
                module = next(
                    key for key, value in MANAGED_COGS.items() if value == cog_name
                )
                await ctx.send(
                    embed=module_disabled_embed(module, ctx.prefix or PREFIX)
                )

    # randomise activity
    async def on_ready(self):
        guild_count = len(self.guilds)
        member_count = sum(
            guild.member_count or 0 for guild in self.guilds
        )

        activity_pool = [
            (discord.ActivityType.watching, f"Helping {guild_count} servers • {PREFIX}help"),
            (discord.ActivityType.playing, f"Playing with {member_count} users"),
            (discord.ActivityType.listening, f"{PREFIX}help in {guild_count} servers"),
            (discord.ActivityType.watching, f"Watching over {member_count} members"),
            (discord.ActivityType.playing, f"Use {PREFIX}help for commands"),
            (discord.ActivityType.listening, f"Available for commands • {PREFIX}help"),
            (discord.ActivityType.watching, f"Check {PREFIX}fl for map rotations!"),
            (discord.ActivityType.watching, f"Use {PREFIX}fl for Frontline maps!"),
        ]
        
        # choose a random activity
        activity_type, activity_name = random.choice(activity_pool)
        activity = discord.Activity(type=activity_type, name=activity_name)

        await self.change_presence(status=discord.Status.online, activity=activity)

        user = self.user
        if user is None:
            logger.error("Miyako is ready, but Discord did not provide the bot user.")
            return

        logger.info(f"Miyako is ready as {user} (ID: {user.id})")
        logger.info(f"Connected to {guild_count} servers with {member_count} members.")


async def main():
    if not BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN missing in .env")
        return

    bot = MiyakoBot()
    async with bot:
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Miyako stopped.")
