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
    print(f"ready {bot.user.name}")

# !say
@bot.command()
async def say(ctx, *, message):
    await ctx.send(message)

# where to send reminders
target_context = None

# reminder every 5 mins
@tasks.loop(minutes=5)
async def reminders():
    if target_context:
        await target_context.send(f"-# what are you doing {target_context.author.mention}")

# !start
@bot.command()
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
async def stop(ctx):
    if reminders.is_running():
        reminders.stop()
        await ctx.send("stopped")
    else:
        await ctx.send("not running")

# !setdelay
@bot.command()
async def setdelay(ctx, minutes: float):
    reminders.change_interval(minutes=minutes)
    clamped = max(0.1, minutes)
    reminders.change_interval(minutes=clamped)
    await ctx.send(f"delay changed to {clamped} minutes")

@bot.command()
async def doing(ctx, *, message):
    filename = datetime.now(timezone).strftime("%m-%d-%Y")
    timestamp = ctx.message.created_at.astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
    with open(f"logs/{filename}.txt", "a") as f:
        f.write(f'{timestamp}: "{message}"\n')
    await ctx.message.add_reaction('🧀')

bot.run(token, log_handler=handler, log_level=logging.DEBUG)