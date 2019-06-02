import discord
from discord.ext import commands
import json
import logging
from .scraper import FormScraper

bot = commands.Bot(command_prefix='!')

responses = {}
questions = {}

with open("config.json") as file:
        config = json.load(file)

scaper_obj = FormScraper(config['url'])

def main():
    logging.basicConfig(level=logging.INFO)
    token = config['token']
    bot.run(token)

def get_questions(form):
    fields = form.fields
    questions = []
    for field in fields:
        if field.type != 'hidden':
            if field.type != 'radio':
                question = field.display + " (type: " + field.type + ")"
                print(question)
                questions.append(question)
            elif field.type == 'radio':
                items = field.display.split(',')
                embed = discord.Embed(
                    title="Respond with one of the options below", colour=0x348DDD)
                print(items)
                for item in items:
                    embed.add_field(name=item, value="-", inline=False)
                questions.append(embed)
    print(questions)
    return questions

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
        author = str(message.author.id)
        if author in responses and len(responses[author]) < len(questions[author]):
            responses[author].append(message.content)
            await mentor_response(message)
            print(responses)

async def mentor_response(message):
    author = str(message.author.id)
    response_length = len(responses[author])
    if response_length < len(questions[author]):
        if isinstance(questions[author][response_length], str):
            print("Rip")
            await message.author.send(questions[author][response_length])
        else:
            print("embed")
            await message.author.send(embed=questions[author][response_length])
    else:
        await message.author.send("Someone will be over to help you shortly!")
        del responses[author]

@bot.command()
async def mentor(ctx):
    print("Mentor triggered")
    form = scaper_obj.extract()
    author = str(ctx.message.author.id)
    responses[author] = ()
    questions[author] = get_questions(form)
    print(questions[author])
    await ctx.author.send("Hello there! I'm here to help")
    await mentor_response(ctx.message)
    await ctx.message.delete()
