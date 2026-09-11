import datetime
import logging
import random
import zoneinfo
from typing import Optional

import aiosqlite
import discord
from discord.ext import commands

from utils.landmine_responses import (
    # system
    already_enabled,
    already_restricted,
    # landmine
    boom_embed,
    channel_status_field,
    config_updated,
    # config
    config_view,
    current_config_field,
    forbidden_timeout,
    global_top,
    # general
    help_embed,
    invalid_setting,
    landmines_enabled,
    landmines_restricted,
    # error
    member_not_found,
    mine_placed,
    mines_cleared,
    missing_permissions,
    missing_value,
    no_danger,
    not_enabled,
    # rateup
    rateup,
    server_stats,
    timeout_maximum,
    timeout_minimum,
    too_powerful,
    unexpected_error,
    # stats
    user_stats,
    value_at_least_one,
    # channels
    whitelisted_channels,
)

DEFAULT_LANDMINE_CHANCE = 100
DEFAULT_TRIGGER_CHANCE = 100
DEFAULT_TIMEOUT_DURATION = 30
RATE_UP_TRIGGER_MULTIPLIER = 5
RATE_UP_HOURS = (0, 3)
DB_PATH = "miyako_data.db"

logger = logging.getLogger("Miyako.Landmine")


class LandmineConfig:
    """Container for per-channel settings."""

    __slots__ = ("channel_id", "landmine_chance", "trigger_chance", "timeout_duration")

    def __init__(
        self,
        channel_id: int,
        landmine_chance: int = DEFAULT_LANDMINE_CHANCE,
        trigger_chance: int = DEFAULT_TRIGGER_CHANCE,
        timeout_duration: int = DEFAULT_TIMEOUT_DURATION,
    ):
        self.channel_id = channel_id
        self.landmine_chance = landmine_chance
        self.trigger_chance = trigger_chance
        self.timeout_duration = timeout_duration


class Landmine(commands.Cog):
    """Landmine module for Miyako."""

    def __init__(self, bot):
        self.bot = bot
        self.tz = zoneinfo.ZoneInfo("Asia/Singapore")
        self._config_cache = {}
        self._active_mines_cache = {}

    async def cog_load(self):
        """Initialise all database tables and warm up the cache."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")

            await db.execute("""
                CREATE TABLE IF NOT EXISTS whitelisted_channels (
                    channel_id INTEGER PRIMARY KEY
                )
            """)
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS landmine_config (
                    channel_id INTEGER PRIMARY KEY,
                    landmine_chance INTEGER DEFAULT {DEFAULT_LANDMINE_CHANCE},
                    trigger_chance INTEGER DEFAULT {DEFAULT_TRIGGER_CHANCE},
                    timeout_duration INTEGER DEFAULT {DEFAULT_TIMEOUT_DURATION},
                    FOREIGN KEY (channel_id) REFERENCES whitelisted_channels(channel_id)
                        ON DELETE CASCADE
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    sent INTEGER DEFAULT 0,
                    triggered INTEGER DEFAULT 0,
                    placed INTEGER DEFAULT 0
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_mines (
                    channel_id INTEGER PRIMARY KEY,
                    count INTEGER DEFAULT 0,
                    FOREIGN KEY (channel_id) REFERENCES whitelisted_channels(channel_id)
                        ON DELETE CASCADE
                )
            """)
            await db.commit()

        # warm the mine cache for all whitelisted channels on startup.
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT channel_id, count FROM active_mines"
            ) as cursor:
                rows = await cursor.fetchall()
                for ch_id, cnt in rows:
                    self._active_mines_cache[ch_id] = cnt

        logger.info("Landmine systems fully initialised.")

    # config helper
    async def _get_config(self, channel_id: int) -> Optional["LandmineConfig"]:
        """Retrieve configuration for a channel. Returns None if not whitelisted."""
        if channel_id in self._config_cache:
            return self._config_cache[channel_id]

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                """
                SELECT w.channel_id,
                       COALESCE(c.landmine_chance, ?),
                       COALESCE(c.trigger_chance, ?),
                       COALESCE(c.timeout_duration, ?)
                FROM whitelisted_channels w
                LEFT JOIN landmine_config c ON w.channel_id = c.channel_id
                WHERE w.channel_id = ?
                """,
                (
                    DEFAULT_LANDMINE_CHANCE,
                    DEFAULT_TRIGGER_CHANCE,
                    DEFAULT_TIMEOUT_DURATION,
                    channel_id,
                ),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                config = LandmineConfig(row[0], row[1], row[2], row[3])
                self._config_cache[channel_id] = config
                return config

    async def _is_whitelisted(self, channel_id: int) -> bool:
        """Shorthand: True if the channel has landmines enabled."""
        return await self._get_config(channel_id) is not None

    # rate-up helper
    def _get_trigger_chance(self, base_chance: int) -> int:
        """Return the effective trigger chance, with rate‑up applied."""
        hour = datetime.datetime.now(self.tz).hour
        if RATE_UP_HOURS[0] <= hour <= RATE_UP_HOURS[1]:
            return max(1, int(base_chance / RATE_UP_TRIGGER_MULTIPLIER))
        return base_chance

    # user stats
    async def _update_user_stat(self, user_id: int, stat_type: str, amount: int = 1):
        """Atomically increment a user statistic."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                f"""
                INSERT INTO user_stats (user_id, {stat_type})
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET {stat_type} = {stat_type} + ?
                """,
                (user_id, amount, amount),
            )
            await db.commit()

    # landmine tracker
    async def _get_active_mines(self, channel_id: int) -> int:
        """Return cached count; fall back to DB if missing."""
        if channel_id not in self._active_mines_cache:
            async with aiosqlite.connect(DB_PATH) as db:
                async with db.execute(
                    "SELECT count FROM active_mines WHERE channel_id = ?",
                    (channel_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    self._active_mines_cache[channel_id] = row[0] if row else 0
        return self._active_mines_cache[channel_id]

    async def _update_active_mines(self, channel_id: int, delta: int):
        """Add delta mines, ensuring minimum of 0."""
        current = await self._get_active_mines(channel_id)
        new = max(0, current + delta)
        self._active_mines_cache[channel_id] = new
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO active_mines (channel_id, count) VALUES (?, ?) "
                "ON CONFLICT(channel_id) DO UPDATE SET count = ?",
                (channel_id, new, new),
            )
            await db.commit()

    async def _set_active_mines(self, channel_id: int, count: int):
        """Set the exact number of mines (≥ 0)."""
        count = max(0, count)
        self._active_mines_cache[channel_id] = count
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO active_mines (channel_id, count) VALUES (?, ?) "
                "ON CONFLICT(channel_id) DO UPDATE SET count = ?",
                (channel_id, count, count),
            )
            await db.commit()

    # listener
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Passive listener: trigger or place mines on every valid message."""
        if message.author.bot or not message.guild:
            return

        config = await self._get_config(message.channel.id)
        if not config:
            return

        # ignore commands
        prefixes = await self.bot.get_prefix(message)
        if isinstance(prefixes, (list, tuple)):
            if message.content.startswith(tuple(prefixes)):
                return
        elif message.content.startswith(prefixes):
            return

        await self._check_landmine(message, config)

    async def _check_landmine(self, message: discord.Message, config: LandmineConfig):
        """Decide whether the message triggers a mine or places a new one."""
        await self._update_user_stat(message.author.id, "sent")

        active = await self._get_active_mines(message.channel.id)

        # trigger a mine if present
        if active > 0:
            trigger_chance = self._get_trigger_chance(config.trigger_chance)
            if random.random() < (1.0 / trigger_chance):
                await self._trigger_landmine(message, config)
                return

        # otherwise, place 1
        if random.random() < (1.0 / config.landmine_chance):
            await self._place_landmine(message, count=1)

    async def _trigger_landmine(self, message: discord.Message, config: LandmineConfig):
        """Apply the timeout and send a boom message."""
        guild = message.guild
        if guild is None:
            return

        member = guild.get_member(message.author.id)
        if not member:
            return await message.channel.send(embed=member_not_found())

        bot_member = guild.me
        if bot_member is None:
            return await message.channel.send(embed=missing_permissions())

        if member.top_role >= bot_member.top_role:
            return await message.channel.send(embed=too_powerful(member))

        if not bot_member.guild_permissions.moderate_members:
            return await message.channel.send(embed=missing_permissions())

        # decrement
        await self._update_active_mines(message.channel.id, -1)

        # timeout the chatter
        try:
            until = discord.utils.utcnow() + datetime.timedelta(
                seconds=config.timeout_duration
            )
            await member.timeout(until, reason="Stepped on a landmine.")
            await self._update_user_stat(member.id, "triggered")

            remaining = await self._get_active_mines(message.channel.id)
            embed = boom_embed(member, config.timeout_duration, remaining)
            await message.channel.send(embed=embed)

        except discord.Forbidden:
            await message.channel.send(embed=forbidden_timeout())
        except Exception as e:
            logger.error(f"Failed to trigger landmine timeout: {e}", exc_info=True)
            await message.channel.send(embed=unexpected_error())

    async def _place_landmine(self, message: discord.Message, count: int = 1):
        """Place hidden mines and notify the channel."""
        await self._update_active_mines(message.channel.id, count)
        await self._update_user_stat(message.author.id, "placed", count)
        await message.channel.send(embed=mine_placed(message.author, count))

    @commands.group(name="landmine", aliases=["lm"], invoke_without_command=True)
    async def landmine_group(self, ctx):
        """Main menu for the landmine game."""
        now = datetime.datetime.now(self.tz)
        in_rateup = RATE_UP_HOURS[0] <= now.hour <= RATE_UP_HOURS[1]
        embed = help_embed(ctx.prefix, now.strftime("%H:%M"), in_rateup)

        if await self._is_whitelisted(ctx.channel.id):
            config = await self._get_config(ctx.channel.id)
            if config is None:
                return await ctx.send(embed=not_enabled())
            active = await self._get_active_mines(ctx.channel.id)
            effective_trigger_chance = self._get_trigger_chance(config.trigger_chance)
            name, value, _ = current_config_field(
                ctx.channel.name,
                {
                    "landmine_chance": config.landmine_chance,
                    "trigger_chance": config.trigger_chance,
                    "timeout_duration": config.timeout_duration,
                },
                active,
                effective_trigger_chance,
            )
            embed.add_field(name=name, value=value, inline=False)
        else:
            name, value, _ = channel_status_field(ctx.prefix)
            embed.add_field(name=name, value=value, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @landmine_group.command(name="allow")
    @commands.has_permissions(administrator=True)
    async def allow_channel(self, ctx):
        """Enable landmines in the current channel."""
        if await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(embed=already_enabled(ctx.channel.mention))

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            # Clean any leftover orphans
            await db.execute(
                "DELETE FROM landmine_config WHERE channel_id = ?", (ctx.channel.id,)
            )
            await db.execute(
                "DELETE FROM active_mines WHERE channel_id = ?", (ctx.channel.id,)
            )
            # Insert
            await db.execute(
                "INSERT INTO whitelisted_channels (channel_id) VALUES (?)",
                (ctx.channel.id,),
            )
            await db.execute(
                """
                INSERT INTO landmine_config
                    (channel_id, landmine_chance, trigger_chance, timeout_duration)
                VALUES (?, ?, ?, ?)
                """,
                (
                    ctx.channel.id,
                    DEFAULT_LANDMINE_CHANCE,
                    DEFAULT_TRIGGER_CHANCE,
                    DEFAULT_TIMEOUT_DURATION,
                ),
            )
            await db.commit()

        self._config_cache.pop(ctx.channel.id, None)
        self._active_mines_cache.pop(
            ctx.channel.id, None
        )  # will be reloaded on next access

        await ctx.send(embed=landmines_enabled(ctx.channel.mention))

    @landmine_group.command(name="restrict")
    @commands.has_permissions(administrator=True)
    async def restrict_channel(self, ctx):
        """Disable landmines and clear all mines from the channel."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(embed=already_restricted(ctx.channel.mention))

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.execute(
                "DELETE FROM active_mines WHERE channel_id = ?", (ctx.channel.id,)
            )
            await db.execute(
                "DELETE FROM landmine_config WHERE channel_id = ?", (ctx.channel.id,)
            )
            await db.execute(
                "DELETE FROM whitelisted_channels WHERE channel_id = ?",
                (ctx.channel.id,),
            )
            await db.commit()

        self._config_cache.pop(ctx.channel.id, None)
        self._active_mines_cache.pop(ctx.channel.id, None)

        await ctx.send(embed=landmines_restricted(ctx.channel.mention))

    @landmine_group.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_mines(self, ctx):
        """Delete all active mines from the channel."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(embed=not_enabled())
        await self._set_active_mines(ctx.channel.id, 0)
        await ctx.send(embed=mines_cleared(ctx.channel.mention))

    @landmine_group.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config_command(
        self, ctx, setting: Optional[str] = None, value: Optional[int] = None
    ):
        """View or change per‑channel landmine settings."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(embed=not_enabled())

        valid = ("landmine_chance", "trigger_chance", "timeout_duration")

        # Show current configuration
        if setting is None:
            config = await self._get_config(ctx.channel.id)
            if config is None:
                return await ctx.send(embed=not_enabled())
            config_dict = {
                "landmine_chance": config.landmine_chance,
                "trigger_chance": config.trigger_chance,
                "timeout_duration": config.timeout_duration,
            }
            return await ctx.send(
                embed=config_view(ctx.prefix, ctx.channel.mention, config_dict)
            )

        setting = setting.lower()
        if setting not in valid:
            return await ctx.send(embed=invalid_setting(valid))

        if value is None:
            return await ctx.send(embed=missing_value(setting, ctx.prefix))

        # Value validation
        if setting in ("landmine_chance", "trigger_chance") and value < 1:
            return await ctx.send(embed=value_at_least_one(setting))

        if setting == "timeout_duration":
            if value < 1:
                return await ctx.send(embed=timeout_minimum())
            if value > 180:
                return await ctx.send(embed=timeout_maximum())

        # Update DB & cache
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                f"""
                INSERT INTO landmine_config (channel_id, {setting})
                VALUES (?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET {setting} = excluded.{setting}
                """,
                (ctx.channel.id, value),
            )
            await db.commit()

        self._config_cache.pop(ctx.channel.id, None)

        await ctx.send(embed=config_updated(setting, value))

    @landmine_group.command(name="drop")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def drop_command(self, ctx, count: int = 1):
        """Manually drop 1‑10 mines."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(embed=not_enabled())

        count = max(1, min(count, 10))
        await self._place_landmine(ctx.message, count)

    @landmine_group.command(name="step")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def step_command(self, ctx):
        """Intentionally time yourself out."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(embed=not_enabled())

        active = await self._get_active_mines(ctx.channel.id)
        if active <= 0:
            return await ctx.send(embed=no_danger())

        config = await self._get_config(ctx.channel.id)
        if config is None:
            return await ctx.send(embed=not_enabled())
        await self._trigger_landmine(ctx.message, config)

    @landmine_group.command(name="check")
    async def check_command(self, ctx):
        """Display how many mines are currently active."""
        active = await self._get_active_mines(ctx.channel.id)
        await ctx.send(
            embed=discord.Embed(
                description=f"There are **{active}** mine(s) in {ctx.channel.mention}",
                colour=0x2F3136,
            )
        )

    @landmine_group.command(name="stats")
    async def stats_command(self, ctx, member: Optional[discord.Member] = None):
        """View landmine statistics for yourself or another member."""
        member = member or ctx.author
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT sent, triggered, placed FROM user_stats WHERE user_id = ?",
                (member.id,),
            ) as cursor:
                row = await cursor.fetchone()
                sent, trig, placed = row if row else (0, 0, 0)

        await ctx.send(embed=user_stats(member, ctx.guild.name, sent, trig, placed))

    @landmine_group.command(name="top")
    async def top_command(self, ctx):
        """Global leaderboard of most triggered users."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id, triggered FROM user_stats ORDER BY triggered DESC LIMIT 10"
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await ctx.send(
                embed=discord.Embed(
                    description="No data recorded yet.", colour=0x2F3136
                )
            )

        entries = []
        for uid, trig in rows:
            user = self.bot.get_user(uid)
            name = user.name if user else f"Unknown ({uid})"
            entries.append((name, trig))

        await ctx.send(embed=global_top(entries))

    @landmine_group.command(name="serverstats", aliases=["guildstats", "ss"])
    async def server_stats_command(self, ctx):
        """Show total landmine activity for the whole server."""
        member_ids = [m.id for m in ctx.guild.members if not m.bot]
        if not member_ids:
            return await ctx.send(
                embed=discord.Embed(
                    description="No human members found in this server.",
                    colour=0x2F3136,
                )
            )

        async with aiosqlite.connect(DB_PATH) as db:
            placeholders = ",".join("?" for _ in member_ids)
            async with db.execute(
                f"""
                SELECT
                    COALESCE(SUM(sent), 0),
                    COALESCE(SUM(triggered), 0),
                    COALESCE(SUM(placed), 0)
                FROM user_stats
                WHERE user_id IN ({placeholders})
                """,
                member_ids,
            ) as cursor:
                row = await cursor.fetchone()
                total_sent, total_triggered, total_placed = (
                    row if row else (0, 0, 0)
                )

            async with db.execute(
                f"""
                SELECT user_id, triggered
                FROM user_stats
                WHERE user_id IN ({placeholders})
                ORDER BY triggered DESC
                LIMIT 5
                """,
                member_ids,
            ) as cursor:
                top_rows = await cursor.fetchall()

        top_users = []
        for uid, trig in top_rows:
            user = ctx.guild.get_member(uid)
            name = user.display_name if user else f"Unknown ({uid})"
            top_users.append(f"**{name}** — {trig}")

        await ctx.send(
            embed=server_stats(
                total_sent,
                total_triggered,
                total_placed,
                top_users,
                ctx.guild.name,
                icon_url=ctx.guild.icon.url if ctx.guild.icon else "",
            )
        )

    @landmine_group.command(name="rateup")
    async def rateup_command(self, ctx):
        """Display the current rate‑up window and multiplier."""
        now = datetime.datetime.now(self.tz)
        hour = now.hour
        in_rateup = RATE_UP_HOURS[0] <= hour <= RATE_UP_HOURS[1]
        await ctx.send(embed=rateup(now.strftime("%H:%M"), in_rateup))

    @landmine_group.command(name="wl", aliases=["list", "whitelist"])
    @commands.has_permissions(manage_guild=True)
    async def list_whitelisted_channels(self, ctx):
        """List all text channels in this server where landmines are enabled."""
        text_channel_ids = [c.id for c in ctx.guild.text_channels]

        if not text_channel_ids:
            return await ctx.send(embed=whitelisted_channels([]))

        placeholders = ",".join("?" for _ in text_channel_ids)
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                f"SELECT channel_id FROM whitelisted_channels WHERE channel_id IN ({placeholders})",
                text_channel_ids,
            ) as cur:
                rows = await cur.fetchall()

        whitelisted = [
            ctx.guild.get_channel(cid) for (cid,) in rows if ctx.guild.get_channel(cid)
        ]

        await ctx.send(embed=whitelisted_channels(whitelisted))
async def setup(bot):
    await bot.add_cog(Landmine(bot))
