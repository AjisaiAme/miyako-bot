import asyncio
import random
import re
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands

from utils.fun_responses import (
    choose_few_options,
    choose_result,
    dice_limit_error,
    flip_guess,
    flip_result,
    invalid_dice,
    poll_cancelled,
    poll_options_count,
    poll_results,
    poll_start,
    random_number,
    random_range_error,
    rate_thing,
    roll_result,
    syntax_error,
    timer_finished,
    timer_range_error,
    timer_start,
)


class PollView(discord.ui.View):
    """Modern voting interface with button-based interaction."""

    def __init__(self, options: list, creator: discord.Member, timeout: int):
        super().__init__(timeout=timeout * 60)
        self.options = options
        self.creator = creator
        self.votes = {option: set() for option in options}
        self.cancelled = False

        for i, option in enumerate(options):
            self.add_item(PollButton(label=option, custom_id=str(i), row=i // 5))

    @discord.ui.button(label="Cancel Poll", style=discord.ButtonStyle.danger, row=2)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.creator.id:
            return await interaction.response.send_message(
                "Only the creator can cancel this.", ephemeral=True
            )
        self.cancelled = True
        self.stop()
        await interaction.response.send_message("Poll cancelled.", ephemeral=True)


class PollButton(discord.ui.Button):
    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if not isinstance(view, PollView):
            return
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, (commands.BadArgument, commands.MissingRequiredArgument)):
            return await ctx.send(embed=syntax_error(ctx.prefix, ctx.command.name))

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
                return await ctx.send(embed=invalid_dice())

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

            details = " ".join(parts).lstrip("+")
            is_d20 = "d20" in dice and total >= 20
            embed = roll_result(total, details, is_d20)
            await ctx.send(embed=embed)

        except ValueError as e:
            await ctx.send(embed=dice_limit_error(str(e)))
        except Exception as e:
            await ctx.send(embed=dice_limit_error(str(e)))

    @commands.command(
        name="poll", help="Starts a button-based poll.", usage='"Question" Opt1 Opt2'
    )
    async def poll(self, ctx, question: str, *options):
        if not 2 <= len(options) <= 10:
            return await ctx.send(embed=poll_options_count())

        view = PollView(list(options), ctx.author, timeout=5)
        msg = await ctx.send(embed=poll_start(question), view=view)
        await view.wait()

        if view.cancelled:
            return await msg.edit(embed=poll_cancelled(ctx.author.mention), view=None)

        total = sum(len(v) for v in view.votes.values())
        results = []
        for opt, vts in view.votes.items():
            pct = (len(vts) / total * 100) if total > 0 else 0
            bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
            results.append(f"**{opt}**\n`{bar}` {len(vts)} ({pct:.0f}%)")

        await msg.edit(embed=poll_results(question, "\n\n".join(results)), view=None)

    @commands.command(
        name="timer", help="Sets a countdown timer.", usage="<minutes> [label]"
    )
    async def timer(self, ctx, minutes: int, *, label: str = "Timer"):
        if not 1 <= minutes <= 360:
            return await ctx.send(embed=timer_range_error())

        end_ts = int(datetime.now(timezone.utc).timestamp() + (minutes * 60))
        msg = await ctx.send(embed=timer_start(label, end_ts))
        await asyncio.sleep(minutes * 60)
        await msg.edit(embed=timer_finished(label, end_ts))
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
            return await ctx.send(embed=choose_few_options())
        await ctx.send(embed=choose_result(random.choice(choices)))

    @commands.command(name="flip", help="Flips a coin.", usage="[heads/tails]")
    async def flip(self, ctx, guess: Optional[str] = None):
        res = random.choice(["Heads", "Tails"])
        if guess and guess.capitalize() in ["Heads", "Tails"]:
            won = guess.capitalize() == res
            embed = flip_guess(res, guess.capitalize(), won)
        else:
            embed = flip_result(res)
        await ctx.send(embed=embed)

    @commands.command(
        name="random", help="Random number generator.", usage="[min] [max]"
    )
    async def random_num(self, ctx, min_n: int = 1, max_n: int = 100):
        if min_n >= max_n:
            return await ctx.send(embed=random_range_error())
        res = random.randint(min_n, max_n)
        await ctx.send(embed=random_number(min_n, max_n, res))

    @commands.command(name="rate", help="Bot rates something.", usage="<thing>")
    async def rate(self, ctx, *, thing: str):
        score = random.randint(1, 10)
        await ctx.send(embed=rate_thing(thing, score))


async def setup(bot):
    await bot.add_cog(Fun(bot))
