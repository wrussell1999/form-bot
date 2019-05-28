import discord
from discord.ext import commands
import json

with open("config.json") as file:
    config = json.load(file)

bot = commands.Bot(command_prefix='!')

def main():
    print("Hello world!")

@bot.event
async def on_ready():
    print("Ready")

@bot.event
async def on_message(message):
    print("hello")
    await message.channel.send("Hello")

@bot.command
async def mentor(ctx):
    ctx.author.send("Hello, how can I help?")
    ctx.message.delete()

token = config['token']
bot.run(token)