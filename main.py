import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

timezone = ZoneInfo("America/Los_Angeles")
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is now running!")

# reply "heck you" when pinged
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user.mentioned_in(message):
        await message.reply(f"heck you", mention_author=False)
    await bot.process_commands(message)

# !say
@bot.command()
# @commands.has_role('grape')
async def say(ctx, *, message):
    await ctx.send(message)

def current_log_path():
    date = datetime.now(timezone).strftime("%m-%d-%Y")
    return f"logs/{date}.txt"

# where to send reminders
target_context = None

# reminder every {current_delay} mins
current_delay = 5.0
@tasks.loop(minutes=current_delay)
async def reminders():
    if target_context:
        await target_context.send(f"-# what are you doing {target_context.author.mention}")

# !start
@bot.command()
@commands.has_role('grape')
async def start(ctx):
    global target_context
    if not reminders.is_running():
        target_context = ctx
        reminders.start()
        await ctx.send("started")
    else:
        await ctx.send("already running")

# !stop
@bot.command()
@commands.has_role('grape')
async def stop(ctx):
    if reminders.is_running():
        reminders.cancel()
        await ctx.send("stopped")
    else:
        await ctx.send("not running")

# !setdelay
@bot.command()
@commands.has_role('grape')
async def setdelay(ctx, minutes: float):
    global current_delay
    current_delay = max(0.1, minutes)
    reminders.change_interval(minutes=current_delay)
    reminders.restart()
    await ctx.send(f"delay changed to {current_delay} minutes")

# !delay
@bot.command()
@commands.has_role('grape')
async def delay(ctx):
    await ctx.send(f"current delay is {current_delay} minutes")

# !doing
@bot.command()
@commands.has_role('grape')
async def doing(ctx, *, message):
    timestamp = ctx.message.created_at.astimezone(timezone).strftime('%I:%M:%S %p')
    with open(current_log_path(), "a") as f:
        f.write(f'{timestamp}: {message}\n')
    await ctx.message.add_reaction('🧀')

# !view
@bot.command()
@commands.has_role('grape')
async def view(ctx, *, message):
    path = current_log_path() # if message.strip() == "today" else f"logs/{message.strip()}"
    try:
        with open(path, "r") as log_file:
            await ctx.send(f"```{log_file.read()}```")
    except FileNotFoundError:
        await ctx.send(f"file '{message.strip()}' not found. usage: `!view mm-dd-yyyy.txt`")

# send heck you to non-grapes
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(f"heck you {ctx.author.mention}")
    else:
        raise error

bot.run(token, log_handler=handler, log_level=logging.DEBUG)