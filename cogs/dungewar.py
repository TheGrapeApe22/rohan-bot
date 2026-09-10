import re
import subprocess
import requests
from discord.ext import commands

class Dungewar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # units
    @staticmethod
    def sanitize_unit(user_input: str) -> str:
        # Only allow alphanumeric, spaces, and specific math/punctuation symbols
        if not re.match(r'^[\w\s\.\+\-\*\/\^\(\)]+$', user_input):
            raise ValueError("Invalid characters detected.")
        
        cleaned = user_input.strip()

        if cleaned.startswith('-'):
            raise ValueError("Flags are not allowed.")
            
        return cleaned

    @commands.hybrid_command(help="Get GNU units response")
    async def units(self, ctx, user_from: str, user_to: str=''):
        if len(user_from) > 1000 or len(user_to) > 1000:
            await ctx.send("Input too long. Please limit to 1000 characters.")
            return
        try:
            cmd = ["units", "-t", self.sanitize_unit(user_from)]
            if user_to:
                cmd.append(self.sanitize_unit(user_to))
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1.0 
            )
            await ctx.send(result.stdout)
        except subprocess.TimeoutExpired:
            await ctx.send("Calculation timed out >:(")
        except ValueError:
            await ctx.send("Nice try. Invalid input.")
        except Exception as e:
            await ctx.send(f"Error doing units: ```{e}```")

    # quote
    @commands.hybrid_command(help="Get dungewar quote of the day")
    async def quote(self, ctx):
        try:
            await ctx.send(requests.get("https://api.dungewar.com/qotd").text)
        except Exception as e:
            await ctx.send(f"error fetching quote: ```{e}```")

    # oil
    @commands.hybrid_command(help="Get oil prices")
    async def oil(self, ctx):
        try:
            res = requests.get("https://api.dungewar.com/oil-full").json()['data']
            change = res['changes']['24h']['percent']
            await ctx.send(f"```diff\n${res['price']} per barrel\n{'+' if change >= 0 else ''}{change}% in the last 24 hours```\n-# (source: [Dungewar API](<https://api.dungewar.com/oil-full>))")
        except Exception as e:
            await ctx.send(f"error fetching oil prices: ```{e}```")

async def setup(bot: commands.Bot):
    await bot.add_cog(Dungewar(bot))
