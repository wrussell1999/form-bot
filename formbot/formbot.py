import discord
from discord.ext import commands
import json

with open("config/config.json") as file:
    config = json.load(file)



def main():
    print("Hello world!")


def on_ready():
    print("Ready")

async def on_message(message):
    await message.channel.send("Hello")

token = config['token']

bot.run(token)