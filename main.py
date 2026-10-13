from datetime import datetime
import traceback

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

from utils.reply import reply
from utils.send import get_command_header, get_command_string, send_log

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

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
    print(f"{bot.user.name} is now running.")

# error handling for all cogs
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRole):
        await reply(ctx.message, f"heck you {ctx.author.mention} (no perms)", )
    else:
        message = f"{get_command_header(ctx.interaction)}Error: ```{''.join(traceback.format_exception(type(error), error, error.__traceback__))}```"
        file_path = f"data/tracebacks/{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.txt"
        with open(file_path, "w") as f:
            f.write(message)
        await send_log('', bot, file=discord.File(file_path))
        raise error

bot.run(
    token,
    log_handler=logging.FileHandler(filename='data/discord.log', encoding='utf-8', mode='w'),
    log_level=logging.DEBUG
)
