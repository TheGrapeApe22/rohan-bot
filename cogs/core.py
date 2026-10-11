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
    async def test1(self, ctx):
        await ctx.defer()
        await send(ctx, "cheese")

    @commands.hybrid_command()
    async def test2(self, ctx):
        await send(ctx, "regular response to test2", ephemeral=True)
        self.cheese = ctx

    @commands.hybrid_command()
    async def test3(self, ctx):
        await send(ctx, "regular response to test3")

    @commands.hybrid_command()
    async def test4(self, ctx):
        await asyncio.sleep(3)
        await self.test3(ctx)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
