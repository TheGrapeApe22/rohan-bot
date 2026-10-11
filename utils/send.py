import os
import discord
from dotenv import load_dotenv
load_dotenv()
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

cache = {}

async def send(ctx: discord.Context, message: str, **kwargs):
    try:
        out = await ctx.send(length_proof(message), **kwargs)
        cache[ctx.channel.id] = ctx
    except discord.errors.NotFound:
        if ctx.channel.id in cache:
            message = f'-# {ctx.author.name} used `{get_command_string(ctx.interaction)}`\n{message}'
            out = await cache[ctx.channel.id].send(length_proof(message), **kwargs)
            return out
        else:
            await send_log(f"failed to send command `{get_command_string(ctx.interaction)}` by {ctx.author.name} (404 + no cached ctx to reply)", ctx.bot)
    return None

async def send_log(message: str, bot: discord.Client):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(length_proof(message))

def get_command_string(interaction: discord.Interaction):
    data = interaction.data
    command_str = "/" + data['name']
    for option in data.get("options", []):
        command_str += f" {option['name']}: {option['value']}"
    return command_str

def length_proof(message: str) -> str:
    if len(message) > 2000:
        return f'-# shortening message to 2000 characters\n{message}'[:2000]
    return message
