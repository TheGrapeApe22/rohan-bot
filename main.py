import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils import reply
from handler import handle_message
import asyncio
import requests

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

timezone = ZoneInfo("America/Los_Angeles")

class CustomCommandTree(discord.app_commands.CommandTree):
    def __init__(self, client: discord.Client):
        super().__init__(
            client,
            allowed_installs=discord.app_commands.AppInstallationType(guild=True, user=True),
            allowed_contexts=discord.app_commands.AppCommandContext(guild=True, dm_channel=True, private_channel=True)
        )
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=['.', '. '], 
            intents=intents,
            help_command=None,
            tree_cls=CustomCommandTree
        )
    async def setup_hook(self):
        await self.load_extension('cogs.reminders')
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

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
@bot.hybrid_command(help="Repeats your message. Usage: `.say <message>`")
async def say(ctx, *, message):
    await ctx.send(message)

def current_log_path():
    date = datetime.now(timezone).strftime("%m-%d-%Y")
    return f"logs/{date}.txt"

def log_path_days_ago(days_ago: int):
    date = (datetime.now(timezone) - timedelta(days=days_ago)).strftime("%m-%d-%Y")
    return f"logs/{date}.txt"

# .ping
@bot.command(help="Pings the sender after 3 seconds. Usage: `.ping`")
async def ping(ctx):
    await asyncio.sleep(3)
    await reply(ctx.message, ctx.author.mention)

# .log
@bot.hybrid_command(help="Logs an event with a timestamp. Usage: `.log <message>`")
@commands.has_role('grape')
async def log(ctx, *, message):
    timestamp = ctx.message.created_at.astimezone(timezone).strftime('%I:%M:%S %p')
    with open(current_log_path(), "a") as f:
        if any(role.name == "invisible logs" for role in ctx.author.roles):
            f.write('*')
        f.write(f'{timestamp} ({ctx.author.name}): {message}\n')
    if ctx.interaction is None:
        await ctx.message.add_reaction('🧀')
    else:
        await ctx.send('🧀')

async def send_log(ctx: commands.Context, message, include_hidden):
    if message is None:
        path = current_log_path()
    else:
        query = message.strip()
        if query.isdigit():
            path = log_path_days_ago(int(query))
        else:
            path = f"logs/{query}.txt"
    path = os.path.realpath(path)
    
    # prevent directory traversal attack
    logs_dir = os.path.realpath('logs')
    if os.path.commonpath([path, logs_dir]) != os.path.commonpath([logs_dir]):
        await reply(ctx.message, "heck you (access denied)")
        return
    try:
        with open(path, "r") as log_file:
            lines = log_file.readlines()
            if not include_hidden:
                lines = [line for line in lines if not line.startswith('*')]

            chunks = []
            current_chunk = []
            current_len = 0
            max_chunk_len = 1500

            for line in lines:
                line_len = len(line)
                if current_chunk and (current_len + line_len > max_chunk_len):
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_len = 0
                current_chunk.append(line)
                current_len += line_len

            if current_chunk:
                chunks.append(current_chunk)

            if not chunks:
                chunks = [["(no visible log lines)\n"]]

            await reply(ctx.message, f"-# {path[-14:-4]}\n```{''.join(chunks[0])}```")
            for chunk in chunks[1:min(6, len(chunks))]: # limit to 6 chunks
                await ctx.send(f"```{''.join(chunk)}```")
    except FileNotFoundError:
        await reply(ctx.message, f"file '{path}' not found. usage: `.view mm-dd-yyyy` or `.view N` (days ago)")
    except Exception as e:
        await reply(ctx.message, f"error: {e}")

# .view
@bot.command(help="Views a log file. usage: `.view mm-dd-yyyy` or `.view N` (days ago)")
async def view(ctx, *, message=None):
    await send_log(ctx, message, include_hidden=False)

# .view2
@bot.command()
@commands.has_role('view2er')
async def view2(ctx, *, message=None):
    await send_log(ctx, message, include_hidden=True)

# servers
@bot.command(help="Lists all servers the bot is in. Usage: `.servers`")
async def servers(ctx):
    guild_names = [guild.name for guild in bot.guilds]
    server_list = "\n".join(guild_names)
    await ctx.send(f"I am in the following {len(bot.guilds)} servers:\n{server_list}")

# quote
@bot.hybrid_command(help="Get dungewar quote of the day")
async def quote(ctx):
    await ctx.send(requests.get("https://api.dungewar.com/qotd").text)
    
@bot.hybrid_command(help="Get oil prices")
async def oil(ctx):
    await ctx.send(requests.get("https://api.dungewar.com/oil-simple").text)

# send heck you to non-grapes
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await reply(ctx.message, f"heck you {ctx.author.mention} (no perms)", )
    else:
        raise error

bot.run(token, log_handler=handler, log_level=logging.DEBUG) # type: ignore
