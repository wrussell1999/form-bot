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
                question = "**Respond with one of the options:**\n- " + field.display
                print(question)
                questions.append(question)
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
        author = str(message.author)
        if author in responses and len(responses[author]) < len(questions[author]):
            responses[author].append(message.content)
            
            await mentor_response(message)
            print(responses)

async def mentor_response(message):
    author = str(message.author)
    if len(responses[author]) < len(questions[author]):
        await message.author.send(questions[author][len(responses[author])])
    else:
        message.author.send("Someone will be over to help you shortly!")

@bot.command()
async def mentor(ctx):
    print("Mentor triggered")
    scaper_obj = FormScraper(config['url'])
    form = scaper_obj.extract()
    author = str(ctx.message.author)
    responses[author] = []
    questions[author] = get_questions(form)
    print(questions[author])
    await ctx.author.send("Hello there! I'm here to help")
    await mentor_response(ctx.message)
    await ctx.message.delete()
