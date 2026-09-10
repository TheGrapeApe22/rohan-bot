import json
from random import random

import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils import reply
import asyncio
try:
    from handler import handle_message # type:ignore
except:
    print('no handler :(')
    pass

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
            tree_cls=CustomCommandTree
        )
    async def setup_hook(self):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'cogs.{filename[:-3]}')
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
    try:
        await handle_message(bot, ctx)
    except:
        pass
    await bot.process_commands(message)

# .say
@bot.hybrid_command(help="Repeats your message. Usage: `.say <message>`")
async def say(ctx, *, message):
    await ctx.send(message)

# .ping
@bot.command(help="Pings the sender after 3 seconds. Usage: `.ping`")
async def ping(ctx):
    await asyncio.sleep(3)
    await reply(ctx.message, ctx.author.mention)

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

bot.run(token, log_handler=handler, log_level=logging.DEBUG) # type: ignore
