import discord
from discord.ext import commands
import json
import logging
import requests
from .scraper import FormScraper

with open("config.json") as file:
    config = json.load(file)

bot = commands.Bot(command_prefix=config['prefix'])
scaper_obj = FormScraper(config['url'])

responses = {}
questions = {}

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
                questions.append(question)
            elif field.type == 'radio':
                items = field.display.split(',')
                embed = discord.Embed(
                    title=config['embed_title'], colour=0x348DDD)
                for index, item in enumerate(items):
                    option = "Option " + str(index + 1)
                    embed.add_field(name=item, value=option, inline=False)
                questions.append(embed)
    return questions

@bot.event
async def on_ready():
    print("Ready")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await bot.process_commands(message)
    if message.guild is None:
        print("DM channel")
        author = str(message.author.id)
        if author in responses and len(responses[author]['responses']) < \
                len(questions[author]['questions']):
            handle_response(message, author)
            await mentor_response(message)
            print(responses)

async def mentor_response(message):
    author = str(message.author.id)
    response_length = len(responses[author]['responses'])
    if response_length < len(questions[author]['questions']):
        if isinstance(questions[author]['questions'][response_length], str):
            await message.author.send(
                questions[author]['questions'][response_length])
        else:
            await message.author.send(
                embed=questions[author]['questions'][response_length])
    else:
        await message.author.send(config['end_message'])
        responses[author]['form'].submit()
        del responses[author]
        del questions[author]

def handle_response(response, author):
    responses[author]['responses'].append(response.content)
    index = len(responses[author]['responses']) - 1
    name = questions[author]['names'][index]
    responses[author]['form'].fill_field(name, response.content)
    print("Response added to field")

@bot.command()
async def mentor(ctx):
    session = requests.session()
    form = scaper_obj.extract(session)

    author = str(ctx.message.author.id)
    responses[author] = {
        "form": form,
        "responses": []
    }
    questions[author] = {
        "questions": get_questions(form),
        "names": [field.name for field in form.fields if not field.hidden]
    }
    print(questions[author])
    await ctx.author.send(config['start_message'])
    await mentor_response(ctx.message)
    await ctx.message.delete()
