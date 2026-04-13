import asyncio
import datetime
import logging
import random
import zoneinfo
from typing import Optional

import aiosqlite
import discord
from discord.ext import commands

from config import EMBED_COLORS, EMOJIS

# Constants
DEFAULT_LANDMINE_CHANCE = 100
DEFAULT_TRIGGER_CHANCE = 100
DEFAULT_TIMEOUT_DURATION = 30
RATE_UP_TRIGGER_MULTIPLIER = 5
RATE_UP_HOURS = (0, 3)
DB_PATH = "yamashiro_data.db"

logger = logging.getLogger("Yamashiro.Landmine")


def create_embed(
    title: str, description: str, color_key="utility", fields=None
) -> discord.Embed:
    """Helper to generate consistent embeds"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLORS.get(color_key, 0x2F3136),
    )
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed


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
    """Watch your step, Milord! Landmine module for Yamashiro."""

    def __init__(self, bot):
        self.bot = bot
        self.tz = zoneinfo.ZoneInfo("Asia/Manila")
        self._cooldowns = {}
        self._config_cache = {}

    async def cog_load(self):
        """Initialize all database tables for the game."""
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
        logger.info("Landmine systems fully initialized.")

    async def _get_config(self, channel_id: int) -> Optional[LandmineConfig]:
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
        """Checks if landmines are enabled in this channel."""
        return await self._get_config(channel_id) is not None

    def _get_trigger_chance(self, base_chance: int) -> int:
        """Determines trigger probability based on time of day (Rate-up hours)."""
        hour = datetime.datetime.now(self.tz).hour
        if RATE_UP_HOURS[0] <= hour <= RATE_UP_HOURS[1]:
            return max(1, int(base_chance / RATE_UP_TRIGGER_MULTIPLIER))
        return base_chance

    async def _update_user_stat(self, user_id: int, stat_type: str, amount: int = 1):
        """Atomically update a user statistic."""
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

    async def _get_active_mines(self, channel_id: int) -> int:
        """Get current number of active mines in a channel."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT count FROM active_mines WHERE channel_id = ?", (channel_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def _update_active_mines(self, channel_id: int, amount: int):
        """Add or remove mines from a channel. Ensures count never goes negative."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO active_mines (channel_id, count)
                VALUES (?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET count = max(0, count + ?)
                """,
                (channel_id, amount, amount),
            )
            await db.commit()

    async def _set_active_mines(self, channel_id: int, count: int):
        """Set the exact number of mines (non‑negative)."""
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT INTO active_mines (channel_id, count)
                VALUES (?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET count = ?
                """,
                (channel_id, max(0, count), max(0, count)),
            )
            await db.commit()

    async def _check_cooldown(
        self, user_id: int, command_name: str, cooldown_seconds: int
    ) -> bool:
        """Return True if user is not on cooldown, else False."""
        key = (user_id, command_name)
        now = datetime.datetime.now().timestamp()
        if key in self._cooldowns:
            if now - self._cooldowns[key] < cooldown_seconds:
                return False
        self._cooldowns[key] = now
        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Passive listener for messages to trigger or place mines."""
        if message.author.bot or not message.guild:
            return

        config = await self._get_config(message.channel.id)
        if not config:
            return

        prefix = await self.bot.get_prefix(message)
        if message.content.startswith(
            tuple(prefix) if isinstance(prefix, (list, tuple)) else prefix
        ):
            return

        await self._check_landmine(message, config)

    async def _check_landmine(self, message: discord.Message, config: LandmineConfig):
        """Logic to decide if a message hits a mine or places a new one."""
        await self._update_user_stat(message.author.id, "sent", 1)
        active_mines = await self._get_active_mines(message.channel.id)

        if active_mines > 0:
            trigger_chance = self._get_trigger_chance(config.trigger_chance)
            if random.random() < (1.0 / trigger_chance):
                await self._trigger_landmine(message, config)
                await self._update_active_mines(message.channel.id, -1)
                return

        if random.random() < (1.0 / config.landmine_chance):
            await self._place_landmine(message, config, count=1)

    async def _trigger_landmine(self, message: discord.Message, config: LandmineConfig):
        """Handles the explosion, timeout, and stat update."""
        member = message.guild.get_member(message.author.id)

        if not member:
            return await message.channel.send(
                embed=create_embed(
                    f"{EMOJIS.get('shield', '🛡️')} Error",
                    "Could not find member.",
                    "warning",
                )
            )

        if member.top_role >= message.guild.me.top_role:
            return await message.channel.send(
                embed=create_embed(
                    f"{EMOJIS.get('shield', '🛡️')} Landmine Defused",
                    f"{member.mention} stepped on a mine, but they are too powerful!",
                    "warning",
                )
            )

        if not message.guild.me.guild_permissions.moderate_members:
            return await message.channel.send(
                embed=create_embed(
                    f"{EMOJIS.get('shield', '🛡️')} Permission Error",
                    "I lack the `Moderate Members` permission to apply timeouts.",
                    "error",
                )
            )

        try:
            until = discord.utils.utcnow() + datetime.timedelta(
                seconds=config.timeout_duration
            )
            await member.timeout(until, reason="Stepped on a landmine.")
            await self._update_user_stat(message.author.id, "triggered", 1)

            remaining = await self._get_active_mines(message.channel.id)

            embed = create_embed(
                f"{EMOJIS.get('boom', '💥')} BOOM!",
                f"{member.mention} stepped on a landmine! They are timed out for **{config.timeout_duration} seconds**\n\n"
                f"💣 **{remaining}** landmine(s) remain",
                "landmine",
            )
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            await message.channel.send(
                embed=create_embed(
                    f"{EMOJIS.get('shield', '🛡️')} Permission Denied",
                    "Eh!? I'm sorry, Milord! I am not allowed to timeout this member.",
                    "error",
                )
            )
        except Exception as e:
            logger.error(f"Failed to trigger landmine timeout: {e}", exc_info=True)
            await message.channel.send(
                embed=create_embed(
                    f"{EMOJIS.get('warning', '⚠️')} Error",
                    "An unexpected error occurred while applying the timeout.",
                    "error",
                )
            )

    async def _place_landmine(
        self, message: discord.Message, config: LandmineConfig, count: int = 1
    ):
        """Places hidden mines in the channel."""
        await self._update_active_mines(message.channel.id, count)
        await self._update_user_stat(message.author.id, "placed", count)
        await message.channel.send(
            embed=create_embed(
                f"{EMOJIS.get('landmine', '💣')} Watch your step, Milord!",
                f"{message.author.mention} just dropped {count} mine(s).",
                "landmine",
            )
        )

    @commands.group(name="landmine", aliases=["lm"], invoke_without_command=True)
    async def landmine_group(self, ctx):
        """Main directory for Landmine commands."""
        embed = create_embed(
            title="💣 Landmine",
            description=(
                "*Watch your step, Milord! Messages may trigger hidden explosives.*\n\n"
                f"Use `{ctx.prefix}lm allow` to enable the game in this channel."
            ),
            color_key="info",
        )

        # Admin commands
        admin_cmds = (
            f"`{ctx.prefix}lm allow` – Enable the module in this channel\n"
            f"`{ctx.prefix}lm restrict` – Disable and remove all mines from current channel\n"
            f"`{ctx.prefix}lm config` – Adjust drop/trigger chances & timeout length\n"
            f"`{ctx.prefix}lm clear` – Remove all active mines"
        )
        embed.add_field(name="Admin Commands", value=admin_cmds, inline=False)

        # Player commands
        user_cmds = (
            f"`{ctx.prefix}lm step` – Intentionally step on a mine (5s cooldown)\n"
            f"`{ctx.prefix}lm drop [1-10]` – Manually place mines (10s cooldown)\n"
            f"`{ctx.prefix}lm check` – See how many mines are active\n"
            f"`{ctx.prefix}lm stats [@user]` – View user stats\n"
            f"`{ctx.prefix}lm serverstats` – View server‑wide stats\n"
            f"`{ctx.prefix}lm top` – View global leaderboard\n"
            f"`{ctx.prefix}lm rateup` – Check for rate-up times"
        )
        embed.add_field(name="Player Commands", value=user_cmds, inline=False)

        # Show current channel configuration if enabled
        if await self._is_whitelisted(ctx.channel.id):
            config = await self._get_config(ctx.channel.id)
            active_mines = await self._get_active_mines(ctx.channel.id)

            config_text = (
                f"**Landmine Odds:** `1 in {config.landmine_chance}` messages\n"
                f"**Trigger Odds:** `1 in {config.trigger_chance}` messages\n"
                f"**Timeout Duration:** `{config.timeout_duration} seconds`\n"
                f"**Active Mines:** {active_mines}"
            )
            embed.add_field(
                name=f"Current Settings for `#{ctx.channel.name}`",
                value=config_text,
                inline=False,
            )
        else:
            embed.add_field(
                name="⚠️ Channel Status",
                value=f"This channel is **not enabled** for landmines.\nUse `{ctx.prefix}lm allow` to activate.",
                inline=False,
            )

        embed.set_footer(
            text=f"Requested by {ctx.author.display_name} • {ctx.prefix}help lm for aliases"
        )
        await ctx.send(embed=embed)

    @landmine_group.command(name="allow")
    @commands.has_permissions(administrator=True)
    async def allow_channel(self, ctx):
        """Enables the landmine system for the current channel."""
        if await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(
                embed=create_embed(
                    "Already Enabled!",
                    f"Landmines are already active in {ctx.channel.mention}, Milord.",
                    "info",
                )
            )

        async with aiosqlite.connect(DB_PATH) as db:
            # Enable foreign keys for this connection
            await db.execute("PRAGMA foreign_keys = ON")

            # Clean up any orphaned rows first (safety measure)
            await db.execute(
                "DELETE FROM landmine_config WHERE channel_id = ?", (ctx.channel.id,)
            )
            await db.execute(
                "DELETE FROM active_mines WHERE channel_id = ?", (ctx.channel.id,)
            )

            # Insert into whitelist
            await db.execute(
                "INSERT INTO whitelisted_channels (channel_id) VALUES (?)",
                (ctx.channel.id,),
            )

            # Insert default config
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

        await ctx.send(
            embed=create_embed(
                "Landmines Enabled!",
                f"Mines are now active in {ctx.channel.mention}. Be careful, Milord!",
                "success",
            )
        )

    @landmine_group.command(name="restrict")
    @commands.has_permissions(administrator=True)
    async def restrict_channel(self, ctx):
        """Disables the landmine system for the current channel."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(
                embed=create_embed(
                    "Already Restricted!",
                    f"Landmines are already disabled in {ctx.channel.mention}, Milord.",
                    "info",
                )
            )

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON")

            # Delete channel from all related tables
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

        await ctx.send(
            embed=create_embed(
                "Landmines Restricted!",
                f"Mines have been cleared from {ctx.channel.mention}. The channel is now safe.",
                "warning",
            )
        )

    @landmine_group.command(name="clear")
    @commands.has_permissions(manage_messages=True)
    async def clear_mines(self, ctx):
        """Remove all active mines from the current channel."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(
                embed=create_embed(
                    "Not Enabled!",
                    "Landmines are not active in this channel.",
                    "warning",
                )
            )
        await self._set_active_mines(ctx.channel.id, 0)
        await ctx.send(
            embed=create_embed(
                "🧹 Mines Cleared",
                f"All active mines have been removed from {ctx.channel.mention}.",
                "success",
            )
        )

    @landmine_group.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config_command(
        self, ctx, setting: Optional[str] = None, value: Optional[int] = None
    ):
        """
        View or change per‑channel landmine settings.
        Settings: landmine_chance, trigger_chance, timeout_duration
        Example: `lm config trigger_chance 50`
        """
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(
                embed=create_embed(
                    "Not Enabled!",
                    "Enable landmines first with `y!lm allow`.",
                    "warning",
                )
            )

        valid_settings = ("landmine_chance", "trigger_chance", "timeout_duration")

        if setting is None:
            config = await self._get_config(ctx.channel.id)

            fields = [
                (
                    "`landmine_chance`",
                    (
                        f"`1 in {config.landmine_chance}` messages\n"
                        f"*Chance for any message to automatically drop a mine.*\n"
                    ),
                    False,
                ),
                (
                    "`trigger_chance`",
                    (
                        f"`1 in {config.trigger_chance}` messages\n"
                        f"*Chance to step on a mine when one is present.*\n"
                    ),
                    False,
                ),
                (
                    "`timeout_duration`",
                    (
                        f"**Current:** `{config.timeout_duration}` seconds\n"
                        f"*How long the user is timed out after triggering a mine.*\n"
                        f"Can be set to a maximum of `180` seconds (3 minutes)."
                    ),
                    False,
                ),
            ]

            embed = create_embed(
                "Landmine Configuration",
                f"Settings for {ctx.channel.mention}\n"
                f"Use `{ctx.prefix}lm config <setting> <value>` to modify.",
                "info",
                fields=fields,
            )
            embed.set_footer(text="Admin only • Changes apply immediately")
            return await ctx.send(embed=embed)

        setting = setting.lower()
        if setting not in valid_settings:
            return await ctx.send(
                embed=create_embed(
                    "Oops!",
                    f"Choose from: {', '.join(valid_settings)}",
                    "error",
                )
            )

        if value is None:
            return await ctx.send(
                embed=create_embed(
                    "Oops!",
                    f"Provide a new value for `{setting}`.\n"
                    f"Example: `{ctx.prefix}lm config {setting} 200`",
                    "error",
                )
            )

        # Validate numeric bounds
        if setting in ("landmine_chance", "trigger_chance") and value < 1:
            return await ctx.send(
                embed=create_embed(
                    "Oops!",
                    f"`{setting}` must be at least 1, Milord.",
                    "error",
                )
            )

        if setting == "timeout_duration":
            if value < 1:
                return await ctx.send(
                    embed=create_embed(
                        "Oops!",
                        "Timeout duration must be at least 1 second, Milord.",
                        "error",
                    )
                )
            if value > 180:  # 3 minutes
                return await ctx.send(
                    embed=create_embed(
                        "Oops!",
                        "Timeout duration cannot exceed 180 seconds (3 minutes), Milord.",
                        "error",
                    )
                )

        # Update database
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
        await ctx.send(
            embed=create_embed(
                "Configuration Updated!",
                f"`{setting}` has been set to `{value}`.",
                "success",
            )
        )

    @landmine_group.command(name="drop")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def drop_command(self, ctx, count: int = 1):
        """Allows a user to manually drop mines (1-10)."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(
                embed=create_embed(
                    "Landmines Restricted!",
                    "Landmines are not active in this channel.",
                    "warning",
                )
            )

        if not await self._check_cooldown(ctx.author.id, "drop", 10):
            return await ctx.send(
                embed=create_embed(
                    "⏳ Cooldown",
                    "C-calm down, Milord! Please wait before placing more mines...",
                    "warning",
                )
            )

        count = max(1, min(count, 10))
        config = await self._get_config(ctx.channel.id)
        await self._place_landmine(ctx.message, config, count)

    @landmine_group.command(name="step")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def step_command(self, ctx):
        """Take a deliberate step to test your luck."""
        if not await self._is_whitelisted(ctx.channel.id):
            return await ctx.send(
                embed=create_embed(
                    "Safe!",
                    "The floor is perfectly safe here, Milord.",
                    "warning",
                )
            )

        if not await self._check_cooldown(ctx.author.id, "step", 5):
            return await ctx.send(
                embed=create_embed(
                    "⏳ Cooldown",
                    "P-please take care, Milord! Wait a moment...",
                    "warning",
                )
            )

        active_mines = await self._get_active_mines(ctx.channel.id)
        if active_mines <= 0:
            return await ctx.send(
                embed=create_embed(
                    "No danger in sight!",
                    "Walk freely, Milord!",
                    "info",
                )
            )

        config = await self._get_config(ctx.channel.id)
        timeout_duration = (
            config.timeout_duration if config else DEFAULT_TIMEOUT_DURATION
        )

        remaining = max(0, active_mines - 1)

        await ctx.send(
            embed=create_embed(
                f"{EMOJIS.get('boom', '💥')} NOOO!",
                f"{ctx.author.mention} intentionally stepped on a landmine! They are timed out for **{timeout_duration} seconds**\n\n"
                f"**{remaining}** landmine(s) remain",
                "landmine",
            )
        )
        await self._trigger_landmine(ctx.message, config)

    @landmine_group.command(name="check")
    async def check_command(self, ctx):
        """Check if mines are enabled and how many are active."""
        active = await self._get_active_mines(ctx.channel.id)

        embed = create_embed(
            f"💣 Landmine Status for {ctx.channel.mention}",
            f"There are **{active}** mine(s) in {ctx.channel.mention}",
            "info",
        )
        await ctx.send(embed=embed)

    @landmine_group.command(name="stats")
    async def stats_command(self, ctx, member: discord.Member = None):
        """View landmine statistics for yourself or another member."""
        member = member or ctx.author
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT sent, triggered, placed FROM user_stats WHERE user_id = ?",
                (member.id,),
            ) as cursor:
                row = await cursor.fetchone()
                sent, trig, placed = row if row else (0, 0, 0)

        fields = [
            ("Messages Sent", f"`{sent}`", True),
            ("Times Triggered", f"`{trig}`", True),
            ("Mines Placed", f"`{placed}`", True),
        ]
        await ctx.send(
            embed=create_embed(
                f"Landmine Stats of `{member.display_name}`",
                f"Activity in `{ctx.guild.name}`",
                fields=fields,
            )
        )

    @landmine_group.command(name="top")
    async def top_command(self, ctx):
        """Displays the global 'Most Stepped On' leaderboard."""
        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute(
                "SELECT user_id, triggered FROM user_stats ORDER BY triggered DESC LIMIT 10"
            ) as cursor:
                rows = await cursor.fetchall()

        if not rows:
            return await ctx.send(
                embed=create_embed(
                    "Global Leaderboard",
                    "No data recorded yet, Milord.",
                    "info",
                )
            )

        leaderboard = []
        for i, (uid, trig) in enumerate(rows, 1):
            user = self.bot.get_user(uid)
            name = user.name if user else f"Unknown ({uid})"
            leaderboard.append(f"{i}. **{name}** — {trig} triggers")

        await ctx.send(
            embed=create_embed(
                "Top Victims",
                "\n".join(leaderboard),
                "info",
            )
        )

    @landmine_group.command(name="serverstats", aliases=["guildstats", "ss"])
    async def server_stats(self, ctx):
        """View total landmine activity across the entire server."""
        # Get all member IDs in the guild (excluding bots)
        member_ids = [m.id for m in ctx.guild.members if not m.bot]

        if not member_ids:
            return await ctx.send(
                embed=create_embed(
                    "Server Stats",
                    "No human members found in this server.",
                    "info",
                )
            )

        async with aiosqlite.connect(DB_PATH) as db:
            # Build placeholders for IN clause
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
                total_sent, total_triggered, total_placed = row

            # server top 5 (LIMIT x)
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

        fields = [
            ("Total Messages Sent", f"`{total_sent}`", True),
            ("Total Mines Triggered", f"`{total_triggered}`", True),
            ("Total Mines Placed", f"`{total_placed}`", True),
        ]

        embed = create_embed(
            f"Landmine Stats for `{ctx.guild.name}`",
            "info",
            fields=fields,
        )

        if top_users:
            embed.add_field(
                name="Top Victims",
                value="\n".join(top_users),
                inline=False,
            )

        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.send(embed=embed)

    @landmine_group.command(name="rateup")
    async def rateup_command(self, ctx):
        """Show current rate‑up status and effective trigger chances."""
        now = datetime.datetime.now(self.tz)
        hour = now.hour
        in_rateup = RATE_UP_HOURS[0] <= hour <= RATE_UP_HOURS[1]

        description = f"Current time: {now.strftime('%H:%M')} (Asia/Manila)\n"
        if in_rateup:
            description += (
                f"🌟 **Rate‑Up Active!** Trigger chance is multiplied by "
                f"1/{RATE_UP_TRIGGER_MULTIPLIER}."
            )
        else:
            description += "Rate‑up is not active. Trigger chances are normal."

        embed = create_embed(
            "⏰ Landmine Rate‑Up",
            description,
            "info" if not in_rateup else "landmine",
            fields=[
                (
                    "Rate‑Up Hours",
                    f"{RATE_UP_HOURS[0]}:00 – {RATE_UP_HOURS[1]}:00",
                    True,
                ),
                ("Multiplier", f"1/{RATE_UP_TRIGGER_MULTIPLIER} of base chance", True),
            ],
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Landmine(bot))
