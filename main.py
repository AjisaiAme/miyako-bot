import asyncio
import logging

import discord
from discord.ext import commands

from config import BOT_TOKEN, PREFIX

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("Yamashiro")


class YamashiroBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        # cog modules
        self.initial_extensions = ["cogs.fun", "cogs.utility", "cogs.landmine"]

    async def setup_hook(self):
        logger.info("Initializing...")
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded: {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    async def on_ready(self):
        # totals of guild (servers) and members
        guild_count = len(self.guilds)
        member_count = sum(guild.member_count for guild in self.guilds)

        # Helping x servers • y!help
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Helping {guild_count} servers • {PREFIX}help",
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

        logger.info(f"Yamashiro is ready as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {guild_count} servers with {member_count} members.")


async def main():
    if not BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN missing in .env")
        return

    bot = YamashiroBot()
    async with bot:
        await bot.start(BOT_TOKEN)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Yamashiro stopped...")
