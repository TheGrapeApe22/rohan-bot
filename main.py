import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from utils import reply
from handler import handle_message
import asyncio

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

timezone = ZoneInfo("America/Los_Angeles")
bot = commands.Bot(command_prefix=['. ', '.'], intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user.name} is now running.") # type: ignore

# reply "heck you" when pinged
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if bot.user.mentioned_in(message): #type: ignore
        await reply(message, f"heck you")
    
    ctx = await bot.get_context(message)
    await handle_message(bot, ctx)
    await bot.process_commands(message)

# .say
@bot.command(help="Repeats your message. Usage: `.say <message>`")
# @commands.has_role('grape')
async def say(ctx, *, message):
    await ctx.send(message)

def current_log_path():
    date = datetime.now(timezone).strftime("%m-%d-%Y")
    return f"logs/{date}.txt"

# .ping
@bot.command(help="Pings the sender after 3 seconds. Usage: `.ping`")
async def ping(ctx):
    await asyncio.sleep(3)
    await reply(ctx.message, ctx.author.mention)

# .log
@bot.command(help="Logs an event with a timestamp. Usage: `.log <message>`")
@commands.has_role('grape')
async def log(ctx, *, message):
    timestamp = ctx.message.created_at.astimezone(timezone).strftime('%I:%M:%S %p')
    with open(current_log_path(), "a") as f:
        f.write(f'{timestamp}: {message}\n')
    await ctx.message.add_reaction('🧀')

# .view
@bot.command(help="Views a log file. Usage: `.view [mm-dd-yyyy]`")
# @commands.has_role('grape')
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

# servers
@bot.command(help="Lists all servers the bot is in. Usage: `.servers`")
async def servers(ctx):
    guild_names = [guild.name for guild in bot.guilds]
    server_list = "\n".join(guild_names)
    await ctx.send(f"I am in the following {len(bot.guilds)} servers:\n{server_list}")

# send heck you to non-grapes
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await reply(ctx.message, f"heck you {ctx.author.mention} (no perms)", )
    else:
        raise error

# prevent commands in DMs
# @bot.check
# async def no_dms(ctx):
#     return ctx.guild is not None

# Load cogs/extensions
@bot.event
async def setup_hook():
    await bot.load_extension('cogs.reminders')

bot.run(token, log_handler=handler, log_level=logging.DEBUG) # type: ignore
