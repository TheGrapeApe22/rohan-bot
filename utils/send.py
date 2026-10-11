import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
load_dotenv()
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

cache = {}

async def send(ctx: commands.Context, message: str=None, **kwargs):
    try:
        if message is not None:
            out = await ctx.send(length_proof(message), **kwargs)
        else:
            out = await ctx.send(**kwargs)
        if (ctx.interaction.is_expired()):
            send_log(f"weird bug: interaction is expired after message sent")
        cache[ctx.channel.id] = ctx
        return out
    except discord.errors.NotFound:
        if ctx.channel.id in cache:
            if message is not None:
                message = length_proof(get_command_header(ctx.interaction) + message)
                return await cache[ctx.channel.id].send(message, **kwargs)
            else:
                return await cache[ctx.channel.id].send(**kwargs)
        else:
            await send_log(f"{get_command_header(ctx.interaction)}failed to send command (404 + no cached ctx to reply)", ctx.bot)
    return None

async def send_log(message: str, bot: discord.Client):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    try:
        await log_channel.send(length_proof(message))
    except Exception:
        print(f"Error in command: {message}")

def get_command_string(interaction: discord.Interaction):
    data = interaction.data
    command_str = "/" + data['name']
    for option in data.get("options", []):
        command_str += f" {option['name']}: {option['value']}"
    return command_str

def get_command_header(interaction: discord.Interaction) -> str:
    return f'-# {interaction.user.name} used `{get_command_string(interaction)}`\n'

def length_proof(message: str) -> str:
    if len(message) > 2000:
        return f'-# shortening message to 2000 characters\n{message}'[:2000]
    return message

async def defer(ctx: commands.Context):
    if not ctx.interaction.response.is_done():
        await ctx.defer()
