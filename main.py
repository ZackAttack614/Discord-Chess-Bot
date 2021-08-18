import json

import discord
import discord_slash

from discord.ext import commands
from calcs import expected_date

with open('secrets.json') as fin:
  secrets = json.load(fin)

bot = commands.Bot(command_prefix='!', help_command=None)
@bot.command(name="willrating")
async def willrating(ctx, name, rating, variant="Rapid"):
  if not rating.isnumeric():
    await ctx.send("Error: Rating must be an integer.")
    return
  error_msg, prob_success, predicted_date = expected_date(name,int(rating),variant)
  if error_msg == 'No error':
    msg = f"{name} {rating} {variant}: {prob_success} chance within 2 years."
    if int(prob_success[:-1]) > 5: msg += f" If success, expected date is {predicted_date}."
    await ctx.send(msg)  
  else:
    await ctx.send(error_msg)

# slash = discord_slash.SlashCommand(bot, sync_commands=True)
# @slash.slash(name="willrating", description="Enter a lichess username and a rating to see the probability you'll achieve the rating, and when you're expected to do so, if ever.")
# async def _willrating(ctx, name, rating, variant="Rapid"):
#   await willrating(ctx, name, rating, variant)

bot.run(secrets.get('discord-token'))
