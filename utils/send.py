import os
import discord

cache = {}

async def send(ctx: discord.Context, message: str, **kwargs):
    try:
        out = await ctx.send(length_proof(message), **kwargs)
        cache[ctx.channel.id] = ctx
    except discord.errors.NotFound:
        if ctx.channel.id in cache:
            message = f'-# {ctx.user.name} used command `{get_command_string(ctx)}`\n{message}'
            out = await cache[ctx.channel.id].send(length_proof(message), **kwargs)
        # else:
        #     print
    return out


LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID")

async def send_log(message: str, bot: discord.Client):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(length_proof(message))

def get_command_string(ctx: discord.Context):
    data = ctx.interaction.data
    command_str = "/" + data['name']
    for option in data.get("options", []):
        command_str += f" {option['name']}: {option['value']}"
    return command_str

def length_proof(message: str) -> str:
    if len(message) > 2000:
        return f'-# shortening message to 2000 characters\n{message}'[:2000]
    return message
