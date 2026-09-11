import asyncio
import logging
import random

import discord
from discord.ext import commands

from config import BOT_TOKEN, PREFIX

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("Miyako")


class MiyakoBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(command_prefix=PREFIX, intents=intents, help_command=None)
        # cog modules
        self.initial_extensions = [
            "cogs.fun",
            "cogs.utility",
            "cogs.landmine",
            "cogs.xiv",
        ]

    async def setup_hook(self):
        logger.info("Initializing...")
        for ext in self.initial_extensions:
            try:
                await self.load_extension(ext)
                logger.info(f"Loaded: {ext}")
            except Exception as e:
                logger.error(f"Failed to load {ext}: {e}")

    # activity
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
