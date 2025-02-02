import discord
from discord.ext import commands
import logging
import requests
import yaml
from .scraper import FormScraper

with open("config.yaml") as file:
    config = yaml.load(file, Loader=yaml.BaseLoader)

bot = commands.Bot(command_prefix=config['discord']['prefix'])

scaper_obj = FormScraper(config['url'])

responses = {}
questions = {}

def main():
    logging.basicConfig(level=logging.INFO)
    token = config['discord']['token']
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
                    title=config['discord']['embed_title'], colour=0x348DDD)
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
    ctx = await bot.get_context(message)

    if ctx.valid:
        print('Command')
        await bot.process_commands(message)
    elif message.channel.type == discord.ChannelType.private:
        print("DM channel")
        author = str(message.author.id)
        if author in responses and len(responses[author]['responses']) < len(questions[author]['questions']):
            print("Message: " + str(message.clean_content))
            handle_response(message, author)
            await mentor_response(message)

def handle_response(response, author):
    responses[author]['responses'].append(response.content)
    index = len(responses[author]['responses']) - 1
    name = questions[author]['names'][index]
    responses[author]['form'].fill_field(name, response.content)
    print("Response added to field")

async def mentor_response(message):
    author = str(message.author.id)
    response_length = len(responses[author]['responses'])

    if response_length < len(questions[author]['questions']):
        if isinstance(questions[author]['questions'][response_length], str):
            await message.author.send(questions[author]['questions'][response_length])
        else:
            await message.author.send(embed=questions[author]['questions'][response_length])
    else:
        await message.author.send(config['discord']['end_message'])
        responses[author]['form'].submit()
        del responses[author]
        del questions[author]

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
    await ctx.author.send(config['discord']['start_message'])

    await mentor_response(ctx.message)
    if ctx.message.channel.type != discord.ChannelType.private:
        await ctx.message.delete()
    print("Mentoring session started with {}".format(ctx.message.author.name))
