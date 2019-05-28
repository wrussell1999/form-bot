import discord
from discord.ext import commands
import json
import logging

bot = commands.Bot(command_prefix='!')

responses = {}

questions = ["What is your issue?", "Where can we find you?", "How can we contact you?"]

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
        if str(message.author) in responses and len(responses[str(message.author)]) < len(questions):
            responses[str(message.author)].append(message.content)
            await mentor_response(message)
            print(responses)

async def mentor_response(message):
    if len(responses[str(message.author)]) < len(questions):
        await message.author.send(questions[len(responses[str(message.author)])])
    else:
        print("done")

@bot.command()
async def mentor(ctx):
    print("Mentor triggered")
    responses[str(ctx.message.author)] = []
    await ctx.author.send("Hello there! I'm here to help")
    await mentor_response(ctx.message)
    await ctx.message.delete()
