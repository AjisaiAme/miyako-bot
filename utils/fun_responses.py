import discord

from .helpers import create_embed

def roll_result(total: int, details: str, is_landmine: bool) -> discord.Embed:
    colour = "landmine" if is_landmine else "fun"
    embed = create_embed("Dice Roll", f"Result: **{total}**", colour_key=colour)
    embed.add_field(name="Details", value=f"```\n{details}\n```")
    return embed


def invalid_dice() -> discord.Embed:
    return create_embed("Error", "Invalid dice format.", colour_key="error")


def dice_limit_error(msg: str) -> discord.Embed:
    return create_embed("Error", msg, colour_key="error")

# poll
def poll_start(question: str) -> discord.Embed:
    return create_embed(f"{question}", "Cast your vote below.", colour_key="utility")


def poll_cancelled(author_mention: str) -> discord.Embed:
    return create_embed(
        "Poll Cancelled", f"Poll closed by {author_mention}", colour_key="landmine"
    )


def poll_results(question: str, results_text: str) -> discord.Embed:
    return create_embed(f"Poll Results: {question}", results_text, colour_key="success")


def poll_options_count() -> discord.Embed:
    return create_embed("Error", "Provide 2-10 options.", colour_key="error")


# timer
def timer_start(label: str, end_ts: int) -> discord.Embed:
    desc = f"**{label}**\nEnds: <t:{end_ts}:t> (<t:{end_ts}:R>)"
    return create_embed("Timer", desc, colour_key="utility")


def timer_finished(label: str, end_ts: int) -> discord.Embed:
    desc = f"**{label}** ended at <t:{end_ts}:t>."
    return create_embed("Timer Complete", desc, colour_key="success")


def timer_range_error() -> discord.Embed:
    return create_embed("Error", "Timer must be 1-360 minutes.", colour_key="error")


# choose
def choose_result(choice: str) -> discord.Embed:
    return create_embed("Selection", f"**{choice}**", colour_key="fun")


def choose_few_options() -> discord.Embed:
    return create_embed("Error", "Provide at least two options.", colour_key="error")


# coin flip
def flip_result(result: str) -> discord.Embed:
    return create_embed("Coin Flip", f"Result: **{result}**", colour_key="utility")


def flip_guess(result: str, guess: str, won: bool) -> discord.Embed:
    desc = f"Guess: **{guess}**\nResult: **{result}**\n\n"
    desc += "Correct." if won else "Incorrect."
    colour = "success" if won else "error"
    return create_embed("Coin Flip", desc, colour_key=colour)


def random_number(min_n: int, max_n: int, result: int) -> discord.Embed:
    specials = {42: "Notable result.", 777: "Notable result."}
    embed = create_embed(
        "🔢 Random Number", f"Range: {min_n}-{max_n}\n# {result}", colour_key="fun"
    )
    if result in specials:
        embed.set_footer(text=specials[result])
    return embed


def random_range_error() -> discord.Embed:
    return create_embed("Error", "Max must be > Min.", colour_key="error")


# rate
def rate_thing(thing: str, score: int) -> discord.Embed:
    embed = create_embed(
        "Rating", f"I'd give **{thing}** a **{score}/10**", colour_key="fun"
    )
    return embed


# ----------------------------------------------------------------------
# Generic / Error
# ----------------------------------------------------------------------
def syntax_error(prefix: str, command_name: str) -> discord.Embed:
    return create_embed(
        "Error",
        f"Incorrect usage. Try `{prefix}help {command_name}`.",
        colour_key="error",
    )
