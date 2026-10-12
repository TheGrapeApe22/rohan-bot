import time

import discord
from discord.ext import commands
from utils.reply import reply
import asyncio

from utils.send import get_command_string, send, send_log

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # reply "heck you" when pinged
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if self.bot.user.mentioned_in(message): #type: ignore
            await reply(message, f"heck you")

    # .say
    @commands.hybrid_command(help="Repeats your message. Usage: `.say <message>`")
    async def say(self, ctx, *, message):
        await send(ctx, message)

    # .ping
    @commands.command(help="Pings the sender after 3 seconds. Usage: `.ping`")
    async def ping(self, ctx):
        await asyncio.sleep(3)
        await reply(ctx.message, ctx.author.mention)

    # servers
    @commands.command(help="Lists all servers the bot is in. Usage: `.servers`")
    async def servers(self, ctx):
        guild_names = [guild.name for guild in self.bot.guilds]
        server_list = "\n".join(guild_names)
        await send(ctx, f"I am in the following {len(self.bot.guilds)} servers:\n{server_list}")

    @commands.hybrid_command()
    async def cheese(self, ctx):
        await send(ctx, "cheese", ephemeral=True)

    @commands.hybrid_command()
    async def test(self, ctx):
        print(ctx.channel)
        msg = await send(ctx, "cheese", ephemeral=True)

        try:
            await ctx.channel.send("This is a test message.", reference=msg)
        except Exception as e:
            print(f"Error sending message: {e}")

        try:
            await msg.reply("This is a test reply.")
        except Exception as e:
            print(f"Error sending message: {e}")

    @commands.hybrid_command()
    async def delay5(self, ctx):
        await asyncio.sleep(5)
        await send(ctx, "5 seconds have passed.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
