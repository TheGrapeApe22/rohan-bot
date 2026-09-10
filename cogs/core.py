from discord.ext import commands
from utils import reply
import asyncio
try:
    from handler import handle_message # type:ignore
except:
    print('no handler :(')
    pass

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
        
        ctx = await self.bot.get_context(message)
        try:
            await handle_message(self.bot, ctx)
        except:
            pass
        await self.bot.process_commands(message)

    # .say
    @commands.hybrid_command(help="Repeats your message. Usage: `.say <message>`")
    async def say(self, ctx, *, message):
        await ctx.send(message)

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
        await ctx.send(f"I am in the following {len(self.bot.guilds)} servers:\n{server_list}")

    # send heck you to non-grapes
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await reply(ctx.message, f"heck you {ctx.author.mention} (no perms)", )
        else:
            raise error

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
