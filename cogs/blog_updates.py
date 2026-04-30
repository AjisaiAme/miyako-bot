import discord
from discord.ext import commands, tasks
import rss_parser as rss
from config import RSS_FEED_URL, RSS_UPDATE_CHANNEL_ID, EMBED_COLORS

class BlogUpdates(commands.Cog):
    """Automatically posts blog updates from the RSS feed."""

    def __init__(self, bot):
        self.bot = bot
        self.last_guid = None  # stored in memory; resets on bot restart (acceptable for a small blog)
        self.check_updates.start()

    def cog_unload(self):
        self.check_updates.cancel()

    @tasks.loop(minutes=15)
    async def check_updates(self):
        """Periodically fetch RSS and post new entries."""
        if RSS_UPDATE_CHANNEL_ID == 0:
            return  # feature disabled

        channel = self.bot.get_channel(RSS_UPDATE_CHANNEL_ID)
        if not channel:
            print(f"RSS update channel {RSS_UPDATE_CHANNEL_ID} not found.")
            return

        try:
            feed = await self.bot.loop.run_in_executor(None, rss.parse, RSS_FEED_URL)
            items = feed.get('items', [])
            if not items:
                return

            # RSS feeds are usually newest first
            latest = items[0]
            latest_guid = latest.get('guid') or latest.get('link')
            if not latest_guid or latest_guid == self.last_guid:
                return

            # New post detected – send embed
            embed = discord.Embed(
                title=latest.get('title', 'New Post'),
                url=latest.get('link'),
                description=latest.get('summary') or latest.get('contentSnippet', '')[:256],
                color=EMBED_COLORS.get('info', 0xA0C4FF),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text='ajisai.ame RSS')

            await channel.send(embed=embed)
            self.last_guid = latest_guid

        except Exception as e:
            print(f"RSS update error: {e}")

    @check_updates.before_loop
    async def before_check_updates(self):
        await self.bot.wait_until_ready()

    @commands.command(name='updates', aliases=['blogupdates', 'blog'])
    async def updates_command(self, ctx):
        """Manually fetch the latest blog posts."""
        try:
            feed = await self.bot.loop.run_in_executor(None, rss.parse, RSS_FEED_URL)
            items = feed.get('items', [])
            if not items:
                return await ctx.send("No posts found.")

            embed = discord.Embed(
                title="Latest Blog Updates",
                color=EMBED_COLORS.get('info', 0xA0C4FF),
                timestamp=discord.utils.utcnow()
            )
            for item in items[:5]:
                embed.add_field(
                    name=item.get('title', 'Untitled'),
                    value=f"{item.get('link')}\n{item.get('summary', '')[:100]}",
                    inline=False
                )
            embed.set_footer(text="From ajisai.ame RSS")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"Failed to fetch updates: {e}")

async def setup(bot):
    await bot.add_cog(BlogUpdates(bot))