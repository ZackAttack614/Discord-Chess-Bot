import json

import discord
import discord_slash

from discord.ext import commands
from calcs import process_inputs

with open('secrets.json') as fin:
  secrets = json.load(fin)

bot = commands.Bot(command_prefix='!', help_command=None)
@bot.command(name="whenrating")
async def whenrating(ctx, name, rating, variant="Rapid"):
  error_msg, prob_success, predicted_date = await process_inputs(name,rating,variant)
  if error_msg == 'No error':
    msg = f"{name}'s chance of reaching {rating} {variant.title()} within 2 years: **{prob_success}**"
    if int(prob_success[:-1]) > 5: msg += f"\nExpected date: **{predicted_date}**."
    await ctx.send(msg)  
  else:
    await ctx.send(error_msg)

# slash = discord_slash.SlashCommand(bot, sync_commands=True)
# @slash.slash(name="whenrating", description="Enter a lichess username and a rating to see the probability you'll achieve the rating, and when you're expected to do so, if ever.")
# async def _whenrating(ctx, name, rating, variant="Rapid"):
#   await whenrating(ctx, name, rating, variant)

bot.run(secrets.get('discord-token'))
