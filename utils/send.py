import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from utils import file_paths as paths

load_dotenv(paths.ENV)
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

ctx_cache = {}

async def _reply(ctx: commands.Context, **kwargs):
    if ctx.interaction:
        return await ctx.send(**kwargs)
    return await ctx.message.reply(**kwargs)

async def send(ctx: commands.Context, message: str=None, **kwargs):
    await defer(ctx, ephemeral=kwargs.get('ephemeral', False))
    try:
        out = await _reply(
            ctx,
            content=length_proof(message) if message is not None else None,
            allowed_mentions=discord.AllowedMentions.none(),
            **kwargs
        )
        ctx_cache[ctx.channel.id] = ctx
        return out
    except discord.errors.NotFound:
        if ctx.channel.id in ctx_cache:
            message = get_command_header(ctx) + (message or '')
            message = length_proof(message)
            try:
                return await ctx_cache[ctx.channel.id].send(
                    message,
                    allowed_mentions=discord.AllowedMentions.none(),
                    **kwargs
                )
            except (discord.errors.NotFound, discord.errors.Forbidden):
                await send_debug_log(f"{get_command_header(ctx)}cached ctx is expired.", ctx.bot)
        else:
            await send_debug_log(f"{get_command_header(ctx)}no cached ctx to send command", ctx.bot)
    return None

async def send_debug_log(message: str, bot: discord.Client, file: discord.File = None):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    try:
        await log_channel.send(
            content=length_proof(message),
            file=file,
            allowed_mentions=discord.AllowedMentions.none()
        )
    except Exception:
        print(f"Error in command: {message}")

def get_command_string(interaction: discord.Interaction):
    data = interaction.data
    command_str = "/" + data['name']
    for option in data.get("options", []):
        command_str += f" {option['name']}: {option['value']}"
    return command_str

def get_command_header(ctx: commands.Context) -> str:
    if ctx.interaction:
        interaction = ctx.interaction
        return f'-# <@{interaction.user.id}> used `{get_command_string(interaction)}`\n'
    else:
        return f'-# <@{ctx.author.id}> used `{ctx.message.content}`\n'

def length_proof(message: str) -> str:
    if len(message) > 2000:
        return f'-# shortening message to 2000 characters\n{message}'[:2000]
    return message

async def defer(ctx: commands.Context, ephemeral: bool = False):
    if ctx.interaction is None:
        return
    if ctx.interaction.response.is_done() or ctx.interaction.is_expired():
        return
    try:
        await ctx.defer(ephemeral=ephemeral)
    except discord.errors.NotFound:
        pass
