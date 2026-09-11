from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord.ext import commands

CURRENT_VERSION = "7.5"

FL_MAP_CYCLE = (
	("Seize", "Seal Rock (Seize)"),
	("Secure", "Secure Ruins (Secure)"),
	("Naadam", "Onsal Hakair (Danshig Naadam)"),
	("Triumph", "Worqor Chirteh (Triumph)"),
	("Seize", "Seal Rock (Seize)"),
	("Shatter", "The Fields of Glory (Shatter)"),
	("Naadam", "Onsal Hakair (Danshig Naadam)"),
	("Triumph", "Worqor Chirteh (Triumph)"),
)
FRONTLINE_ANCHOR = datetime(2026, 9, 10, 15, tzinfo=timezone.utc)
ROTATION_INTERVAL = timedelta(days=1)
FRONTLINE_ASSETS = {
	"Seal Rock (Seize)": "seal-rock.png",
	"Secure Ruins (Secure)": "secure-ruins.png",
	"Onsal Hakair (Danshig Naadam)": "onsal-hakair.png",
	"Worqor Chirteh (Triumph)": "worqor-chirteh.png",
	"The Fields of Glory (Shatter)": "fields-of-glory.png",
}
FRONTLINE_ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "frontline"


class XIV(commands.Cog):
	"""Final Fantasy XIV PvP utilities."""

	@staticmethod
	def frontline_rotation(now=None):
		now = now or datetime.now(timezone.utc)
		elapsed = now - FRONTLINE_ANCHOR
		rotation_index, _ = divmod(
			int(elapsed.total_seconds()), int(ROTATION_INTERVAL.total_seconds())
		)
		current_index = rotation_index % len(FL_MAP_CYCLE)
		next_rotation = FRONTLINE_ANCHOR + (rotation_index + 1) * ROTATION_INTERVAL
		return current_index, next_rotation

	@commands.command(
		name="frontline",
		aliases=["fl"],
		help="Shows the current Frontline map and upcoming rotation.",
	)
	async def frontline(self, ctx):
		now = datetime.now(timezone.utc)
		current_index, next_rotation = self.frontline_rotation(now)
		current_short, current_map = FL_MAP_CYCLE[current_index]
		remaining = max(0, int((next_rotation - now).total_seconds()))
		hours, remainder = divmod(remaining, 3600)
		minutes, seconds = divmod(remainder, 60)
		image_name = FRONTLINE_ASSETS[current_map]
		image_path = FRONTLINE_ASSET_DIR / image_name

		schedule = []
		for offset in range(7):
			_, map_name = FL_MAP_CYCLE[
				(current_index + offset + 1) % len(FL_MAP_CYCLE)
			]
			rotation_time = next_rotation + offset * ROTATION_INTERVAL
			schedule.append(f"<t:{int(rotation_time.timestamp())}:D> {map_name}")
		rotation_end = next_rotation + 6 * ROTATION_INTERVAL
		date_range = (
			f"{next_rotation.strftime('%d')} - "
			f"{rotation_end.strftime('%d %B %Y')}"
		)

		embed = discord.Embed(
			title=f"Frontline Tracker - Patch {CURRENT_VERSION}",
			color=discord.Color.blue(),
		)
		embed.add_field(name="Current Map", value=f"**{current_short}**\n{current_map}")
		embed.add_field(
			name="Next Rotation",
			value=f"<t:{int(next_rotation.timestamp())}:R>\n"
			f"`{hours:02d}:{minutes:02d}:{seconds:02d}`",
		)
		embed.add_field(
			name=f"Rotation Schedule for {date_range}",
			value="  •  ".join(name for name, _ in FL_MAP_CYCLE),
			inline=False,
		)
		embed.add_field(name="Upcoming Maps", value="\n".join(schedule), inline=False)
		embed.set_image(url=f"attachment://{image_name}")
		embed.set_footer(
			text=f"{now.strftime('%d %B %Y')} • Maps rotate daily at 15:00 UTC"
		)
		await ctx.send(file=discord.File(image_path, filename=image_name), embed=embed)


async def setup(bot):
	await bot.add_cog(XIV(bot))
