import discord
from discord.ext import commands
import json
import logging

with open("config.json") as file:
    config = json.load(file)

logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix='!')

def main():
    print("Hello world!")

@bot.event
async def on_ready():
    print("Ready")

@bot.event
async def on_message(message):
    if (message.author.bot):
        return
    await bot.process_commands(message)
    await message.channel.send("I am Groot")

@bot.command()
async def mentor(ctx):
    print("hello")
    await ctx.author.send("Hello, how can I help?")
    await ctx.message.delete()

token = config['token']
bot.run(token)
