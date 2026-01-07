import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import reply

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

timezone = ZoneInfo("America/Los_Angeles")
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is now running.")

# reply "heck you" when pinged
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user.mentioned_in(message):
        await reply(message, f"heck you")
    await bot.process_commands(message)

# .say
@bot.command()
# @commands.has_role('grape')
async def say(ctx, *, message):
    await ctx.send(message)

def current_log_path():
    date = datetime.now(timezone).strftime("%m-%d-%Y")
    return f"logs/{date}.txt"

# .log
@bot.command()
@commands.has_role('grape')
async def log(ctx, *, message):
    timestamp = ctx.message.created_at.astimezone(timezone).strftime('%I:%M:%S %p')
    with open(current_log_path(), "a") as f:
        f.write(f'{timestamp}: {message}\n')
    await ctx.message.add_reaction('🧀')

# .view
@bot.command()
@commands.has_role('grape')
async def view(ctx, *, message=None):
    path = current_log_path() if message is None else f"logs/{message.strip()}.txt"
    path = os.path.realpath(path)
    
    # prevent directory traversal attack
    logs_dir = os.path.realpath('logs')
    if os.path.commonpath([path, logs_dir]) != os.path.commonpath([logs_dir]):
        await reply(ctx.message, "heck you (access denied)")
        return
    try:
        with open(path, "r") as log_file:
            await reply(ctx.message, f"```{log_file.read()}```")
    except FileNotFoundError:
        await reply(ctx.message, f"file '{path}' not found. usage: `.view mm-dd-yyyy.txt`")
    except Exception as e:
        await reply(ctx.message, f"error: {e}")
# send heck you to non-grapes
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await reply(ctx.message, f"heck you {ctx.author.mention} (no perms)", )
    else:
        raise error

# Load cogs/extensions
@bot.event
async def setup_hook():
    # Reminders cog contains: start, stop, setdelay, delay
    await bot.load_extension('cogs.reminders')

bot.run(token, log_handler=handler, log_level=logging.DEBUG)