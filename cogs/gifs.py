import discord
from discord.ext import commands

class Gifs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(help="david reaction gif")
    async def david_reaction(self, ctx):
        await ctx.send(file=discord.File("assets/gifs/david-reaction.gif"))

    @commands.hybrid_command(help="bk boykisser zoom in gif")
    async def bk(self, ctx):
        await ctx.send(file=discord.File("assets/gifs/boykisser-zoom.gif"))

    @commands.hybrid_command(help="bk boykisser lick gif")
    async def bk_lick(self, ctx):
        await ctx.send("https://tenor.com/view/licky-mauzymice-boykisser-gif-1303620811246816055")

    @commands.hybrid_command(help="bk boykisser meow mao kiss gif")
    async def bk_meow(self, ctx):
        await ctx.send("https://tenor.com/view/boy-kisser-kiss-cute-gif-12091707061489691944")

    @commands.hybrid_command(help="bk boykisser smirk smile gif")
    async def bk_smirk(self, ctx):
        await ctx.send("https://tenor.com/view/boykisser-gif-16777119058470997423")
        
    @commands.hybrid_command(help="bk boykisser spin gif")
    async def bk_spin(self, ctx):
        await ctx.send("https://tenor.com/view/boykisser-spin-silly-cat-silly-cat-gif-15869807335045066863")
    @commands.hybrid_command(help="bk boykisser mindustry gif")
    async def bk_mindustry(self, ctx):
        await ctx.send("https://tenor.com/view/mindustry-mindustry-rp-mindustry-roleplay-mindustry-qw-mindustry-quantum-well-gif-8979957206124813591")

    @commands.hybrid_command(help="bk boykisser blushing embarrassed gif")
    async def bk_blushing(self, ctx):
        await ctx.send("https://tenor.com/view/boy-kisser-blushing-cute-gif-5271857668865124738")

    @commands.hybrid_command(help="bk boykisser stare gif")
    async def bk_stare(self, ctx):
        await ctx.send("https://klipy.com/gifs/boykisser-boy-kisser")

    @commands.hybrid_command(help="bk boykisser touch boop nose blush gif")
    async def bk_boop(self, ctx):
        await ctx.send("https://klipy.com/gifs/crystal-the-cavern-spirit-28")

    @commands.hybrid_command(help="bk boykisser cry sad tear gif")
    async def bk_sad(self, ctx):
        await ctx.send("https://klipy.com/gifs/boykisser-boy-kisser-10")

    @commands.hybrid_command(help="bk boykisser big eyes mesmerized blinking smooth brain kitty gif")
    async def bk_eyes(self, ctx):
        await ctx.send("https://klipy.com/gifs/smooth-brain-kitty")

    @commands.hybrid_command(help="mindustry my honest reactor reaction gif")
    async def bk_honest_reaction(self, ctx):
        await ctx.send("https://klipy.com/gifs/my-honest-reaction-my-honest-reactor-1")

async def setup(bot: commands.Bot):
    await bot.add_cog(Gifs(bot))
