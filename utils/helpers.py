import discord

COLOURS = {
    "default": 0xFFFFFF,
    "info": 0x2F3136,
    "success": 0x57F287,
    "warning": 0xFEE75C,
    "error": 0xED4245,
    "fun": 0x5865F2,
    "utility": 0x2F3136,
    "landmine": 0xE57373,
}


def create_embed(
    title: str,
    description: str,
    colour_key: str = "default",
    fields: list[tuple[str, str, bool]] | None = None,
) -> discord.Embed:
    """Build a consistent Discord embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        colour=COLOURS.get(colour_key, COLOURS["default"]),
        timestamp=discord.utils.utcnow(),
    )
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    return embed
