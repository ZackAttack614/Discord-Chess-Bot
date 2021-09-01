import json

import discord
from discord.ext import commands
from calcs import process_inputs

with open('secrets.json') as fin:
    secrets = json.load(fin)

bot = commands.Bot(command_prefix='!', help_command=None)
@bot.command(name="whenrating")
async def whenrating(ctx, name, rating, variant="Rapid"):
    error_bool, error_msg, prob_success, predicted_date = await process_inputs(name,rating,variant)
    # Error that is so severe that no prediction is generated
    if error_bool and prob_success is None:
        await ctx.send(error_msg)
    else:
        msg = ""
        # Warning, there's something concerning but we can still display a prediction
        if error_bool:
            msg += error_msg + '\n'
        msg += f"{name}'s chance of reaching {rating} {variant.title()} within 2 years: **{prob_success}%**"
        if prob_success > 5:
            msg += f"\nExpected date: **{predicted_date}**."
        await ctx.send(msg)
        

bot.run(secrets.get('discord-token'))
