import asyncio
import random
import re
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

from config import EMBED_COLORS, EMOJIS, PREFIX


class PollView(discord.ui.View):
    """Modern voting interface with button-based interaction."""

    def __init__(self, options: list, creator: discord.Member, timeout: int):
        super().__init__(timeout=timeout * 60)
        self.options = options
        self.creator = creator
        self.votes = {option: set() for option in options}
        self.canceled = False

        for i, option in enumerate(options):
            self.add_item(PollButton(label=option, custom_id=str(i), row=i // 5))

    @discord.ui.button(label="Cancel Poll", style=discord.ButtonStyle.danger, row=2)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator.id:
            return await interaction.response.send_message(
                "Only the creator can cancel this.", ephemeral=True
            )
        self.canceled = True
        self.stop()
        await interaction.response.send_message("Poll canceled.", ephemeral=True)


class PollButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        for opt in view.votes:
            if interaction.user.id in view.votes[opt]:
                view.votes[opt].remove(interaction.user.id)
        view.votes[self.label].add(interaction.user.id)
        await interaction.response.send_message(
            f"Voted for **{self.label}**", ephemeral=True
        )


class Fun(commands.Cog):
    """Entertainment and utility modules."""

    def __init__(self, bot):
        self.bot = bot

    def embed(self, title: str, desc: str, color_key="info"):
        """Generates an embed using the central EMBED_COLORS from config."""
        return discord.Embed(
            title=title,
            description=desc,
            color=EMBED_COLORS.get(color_key, EMBED_COLORS.get("info", 0xA0C4FF)),
        )

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
            return await ctx.send(
                embed=self.embed(
                    "⚠️ Syntax Error",
                    f"Incorrect usage. Try `{ctx.prefix}help {ctx.command}`.",
                    "error",
                )
            )

    @commands.command(
        name="roll",
        aliases=["d"],
        help="Rolls dice with modifiers.",
        usage="[expression] (e.g. 2d20 + 5)",
    )
    async def roll(self, ctx, *, dice: str = "1d6"):
        try:
            dice = dice.replace(" ", "").lower()
            pattern = r"([+-]?)(\d*)d(\d+)|([+-]?\d+)"
            matches = re.findall(pattern, dice)
            if not matches:
                return await ctx.send("Invalid dice format.")
            total, parts = 0, []
            for sign, count, sides, mod in matches:
                mult = -1 if sign == "-" else 1
                if sides:
                    c, s = int(count or 1), int(sides)
                    if c > 50 or s > 1000:
                        raise ValueError("Limit: 50d1000.")
                    rolls = [random.randint(1, s) for _ in range(c)]
                    total += sum(rolls) * mult
                    parts.append(f"{sign or '+'}{c}d{s} ({', '.join(map(str, rolls))})")
                else:
                    total += int(mod)
                    parts.append(f"{int(mod):+d}")

            color = "landmine" if "d20" in dice and total >= 20 else "fun"
            e = self.embed("🎲 Dice Roll", f"Result: **{total}**", color)
            e.add_field(
                name="Details", value=f"```fix\n{' '.join(parts).lstrip('+')}```"
            )
            await ctx.send(embed=e)
        except Exception as err:
            await ctx.send(embed=self.embed("❌ Error", str(err), "error"))

    @commands.command(
        name="poll", help="Starts a button-based poll.", usage='"Question" Opt1 Opt2'
    )
    async def poll(self, ctx, question: str, *options):
        if not 2 <= len(options) <= 10:
            return await ctx.send("Provide 2-10 options.")
        view = PollView(options, ctx.author, timeout=5)
        msg = await ctx.send(
            embed=self.embed(f"📊 {question}", "Cast your vote below.", "utility"),
            view=view,
        )
        await view.wait()
        if view.canceled:
            return await msg.edit(
                embed=self.embed(
                    "🚫 Canceled", f"Poll closed by {ctx.author.mention}", "landmine"
                ),
                view=None,
            )
        results, total = [], sum(len(v) for v in view.votes.values())
        for opt, vts in view.votes.items():
            pct = (len(vts) / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            results.append(f"**{opt}**\n`{bar}` {len(vts)} ({pct:.0f}%)")
        await msg.edit(
            embed=self.embed(
                f"✅ Results: {question}", "\n\n".join(results), "success"
            ),
            view=None,
        )

    @commands.command(
        name="timer", help="Sets a countdown timer.", usage="<minutes> [label]"
    )
    async def timer(self, ctx, minutes: int, *, label: str = "Timer"):
        if not 1 <= minutes <= 360:
            return await ctx.send("Timer must be 1-360 minutes.")
        end_ts = int(datetime.now(timezone.utc).timestamp() + (minutes * 60))
        e = self.embed(
            "⏳ Timer Active",
            f"**{label}**\nEnds: <t:{end_ts}:t> (<t:{end_ts}:R>)",
            "utility",
        )
        msg = await ctx.send(embed=e)
        await asyncio.sleep(minutes * 60)
        await msg.edit(
            embed=self.embed(
                "🔔 Timer Finished",
                f"**{label}** is done!\nEnded at: <t:{end_ts}:t>",
                "success",
            )
        )
        await ctx.send(
            f"🔔 {ctx.author.mention}, your timer for **{label}** is up!",
            delete_after=60,
        )

    @commands.command(
        name="choose", help="Picks an item from a list.", usage="item1, item2"
    )
    async def choose(self, ctx, *, options: str):
        delim = ";" if ";" in options else ","
        choices = [c.strip() for c in options.split(delim) if c.strip()]
        if len(choices) < 2:
            return await ctx.send("Provide at least two options.")
        await ctx.send(
            embed=self.embed(
                "⚖️ Selection", f"I'll go with: **{random.choice(choices)}**", "fun"
            )
        )

    @commands.command(name="flip", help="Flips a coin.", usage="[heads/tails]")
    async def flip(self, ctx, guess: str = None):
        res = random.choice(["Heads", "Tails"])
        e = self.embed("🪙 Coin Flip", f"It's **{res}**!", "utility")
        if guess and guess.capitalize() in ["Heads", "Tails"]:
            win = guess.capitalize() == res
            e.description = (
                f"Guess: **{guess.capitalize()}**\nResult: **{res}**\n\n"
                + ("✨ Correct!" if win else "❌ Wrong.")
            )
            e.color = EMBED_COLORS["success"] if win else EMBED_COLORS["error"]
        await ctx.send(embed=e)

    @commands.command(
        name="random", help="Random number generator.", usage="[min] [max]"
    )
    async def random_num(self, ctx, min_n: int = 1, max_n: int = 100):
        if min_n >= max_n:
            return await ctx.send("Max must be > Min.")
        res = random.randint(min_n, max_n)
        e = self.embed("🔢 Random Number", f"Range: {min_n}-{max_n}\n# {res}", "fun")
        specials = {42: "The meaning of life.", 69: "Nice.", 777: "Jackpot!"}
        if res in specials:
            e.set_footer(text=specials[res])
        await ctx.send(embed=e)

    @commands.command(name="rate", help="Bot rates something.", usage="<thing>")
    async def rate(self, ctx, *, thing: str):
        score = random.randint(1, 10)
        e = self.embed("⭐ Rating", f"I'd give **{thing}** a **{score}/10**", "fun")
        if score == 10:
            e.set_footer(text="Absolute perfection.")
        await ctx.send(embed=e)


async def setup(bot):
    await bot.add_cog(Fun(bot))
