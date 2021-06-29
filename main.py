import json

import discord
import discord_slash

from discord.ext import commands
from calcs import expected_date

with open('secrets.json') as fin:
  secrets = json.load(fin)

bot = commands.Bot(command_prefix='!', help_command=None)
@bot.command(name="whenrating")
async def whenrating(ctx, name, rating, variant="Rapid"):
  if not rating.isnumeric():
    await ctx.send("Error: Rating must be an integer.")
    return
  date = await expected_date(name, int(rating), variant)
  if date == None:
    await ctx.send(f"Error: Not enough rating history for **{variant}** for **{name}**!")
    return
  elif date == -1:
    await ctx.send(f"Error: No lichess user with name **{name}**!")
    return
  await ctx.send(f'{name} can expect to have a {variant} rating of {rating} on {date.strftime("%b %d, %Y")}.')

slash = discord_slash.SlashCommand(bot, sync_commands=True)
@slash.slash(name="whenrating", description="Enter a lichess username and a rating to see the expected time when that rating will be achieved.")
async def _whenrating(ctx, name, rating, variant="Rapid"):
  await whenrating(ctx, name, rating, variant)

bot.run(secrets.get('discord-token'))
