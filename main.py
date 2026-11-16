from datetime import datetime
import traceback

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

from utils.send import get_command_header, send, send_debug_log
from utils.generate_memes import generate as generate_memes
from utils import file_paths as paths

load_dotenv(paths.ENV)
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
        try:
            generate_memes()
        except Exception as e:
            print(f"Error during initialization: {e}")
    async def setup_hook(self):
        for cog_file in paths.COGS.glob('*.py'):
            await self.load_extension(f'cogs.{cog_file.stem}')
        await self.tree.sync()
        print(f"Synced slash commands for {self.user}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"{bot.user.name} is now running.")

def _error_is(error, *types):
    while hasattr(error, 'original'):
        error = error.original
    return isinstance(error, *types)

# error handling for all cogs
@bot.event
async def on_command_error(ctx, error):
    if _error_is(error, commands.MissingRole):
        await send(ctx, f"heck you {ctx.author.mention} (no perms)", )
    elif _error_is(error, PermissionError):
        await send_debug_log(f'{get_command_header(ctx)}PermissionError: {error}', bot)
    else:
        # write the error to a file and send it
        paths.TRACEBACKS.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        file_path = paths.TRACEBACKS / f"{timestamp}.txt"
        file_path.write_text(''.join(traceback.format_exception(type(error), error, error.__traceback__)))
        
        await send_debug_log(f'{get_command_header(ctx)}Error: ', bot, file=discord.File(file_path))
        raise error

bot.run(
    token,
    log_handler=logging.FileHandler(filename=paths.DISCORD_LOG, encoding='utf-8', mode='w'),
    log_level=logging.DEBUG
)
