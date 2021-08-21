import json

import discord
import discord_slash

from discord.ext import commands
from calcs import process_inputs

with open('secrets.json') as fin:
  secrets = json.load(fin)

bot = commands.Bot(command_prefix='!', help_command=None)
@bot.command(name="willrating")
async def willrating(ctx, name, rating, variant="Rapid"):
  error_msg, prob_success, predicted_date = process_inputs(name,rating,variant)
  if error_msg == 'No error':
    msg = f"{name} {rating} {variant.title()}: {prob_success} chance within 2 years."
    if int(prob_success[:-1]) > 5: msg += f" If user succeeds, expected date is {predicted_date}."
    await ctx.send(msg)  
  else:
    await ctx.send(error_msg)

# slash = discord_slash.SlashCommand(bot, sync_commands=True)
# @slash.slash(name="willrating", description="Enter a lichess username and a rating to see the probability you'll achieve the rating, and when you're expected to do so, if ever.")
# async def _willrating(ctx, name, rating, variant="Rapid"):
#   await willrating(ctx, name, rating, variant)

bot.run(secrets.get('discord-token'))
