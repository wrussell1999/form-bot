import discord
from discord.ext import commands
import json
import logging

bot = commands.Bot(command_prefix='!')

users = {

}

def main():
    with open("config.json") as file:
        config = json.load(file)
    logging.basicConfig(level=logging.INFO)
    token = config['token']
    bot.run(token)

@bot.event
async def on_ready():
    print("Ready")

@bot.event
async def on_message(message):
    print("message: " + message.content + ", channel: " + str(message.channel), ", author: "  + str(message.author))
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.guild is None:
        print("DM channel")

@bot.command()
async def mentor(ctx):
    print("Mentor triggered")
    await ctx.author.send("Hello, how can I help?")
    await ctx.message.delete()
