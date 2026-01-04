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
bot = commands.Bot(command_prefix='.', intents=intents)

def reply(message, reply_text):
    return message.reply(reply_text, mention_author=False)

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

# where to send reminders
target_context = None
last_reminder = None

# reminder every {current_delay} mins
current_delay = 5.0
@tasks.loop(minutes=current_delay)
async def reminders():
    global last_reminder
    if target_context:
        if last_reminder:
            await last_reminder.delete()
        last_reminder = await reply(target_context, f"-# what are you doing {target_context.author.mention} ({reminders.current_loop})")
        

# .start
@bot.command()
@commands.has_role('grape')
async def start(ctx):
    global target_context
    if not reminders.is_running():
        target_context = ctx
        reminders.start()
        await reply(ctx.message, "started")
    else:
        await reply(ctx.message, "already running")

# .stop
@bot.command()
@commands.has_role('grape')
async def stop(ctx):
    if reminders.is_running():
        reminders.cancel()
        await reply(ctx.message, "stopped")
    else:
        await reply(ctx.message, "not running")

# .setdelay
@bot.command()
@commands.has_role('grape')
async def setdelay(ctx, minutes: float):
    global current_delay
    current_delay = max(0.1, minutes)
    reminders.change_interval(minutes=current_delay)
    reminders.restart()
    await reply(ctx.message, f"delay changed to {current_delay} minutes")

# .delay
@bot.command()
@commands.has_role('grape')
async def delay(ctx):
    await reply(ctx.message, f"current delay is {current_delay} minutes")

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

bot.run(token, log_handler=handler, log_level=logging.DEBUG)