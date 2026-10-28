import re
import subprocess
import requests
from discord.ext import commands
from utils.send import send, defer
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
            await send(ctx, "Input too long. Please limit to 1000 characters.")
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
            await send(ctx, result.stdout)
        except subprocess.TimeoutExpired:
            await send(ctx, "Calculation timed out >:(")
        except ValueError:
            await send(ctx, "Nice try. Invalid input.")
        except Exception as e:
            await send(ctx, f"Error doing units: ```{e}```")

     # quote
    @commands.hybrid_command(help="Get dungewar quote of the day")
    async def quote(self, ctx):
        try:
            await defer(ctx)
            res = requests.get("https://api.dungewar.com/qotd-full").json()
            quote_text = res.get("quote", "").strip()
            author = res.get("author", "").strip()
            image = res.get("image", "").strip()
            comment = res.get("comment", "").strip() if res.get("comment") else ""

            clean_quote = quote_text.strip(" \"'")
            if author:
                msg = f"> *\"{clean_quote}\"*\n> — **{author}**"
            else:
                msg = f"> *\"{clean_quote}\"*"

            if comment:
                comment_lines = "\n".join(f"> *{line}*" if line.strip() else ">" for line in comment.splitlines())
                msg += f"\n\n{comment_lines}"

            if image:
                msg += f"\n-# (source: [Dungewar AP](<https://api.dungewar.com/qotd-full>)[I]({image})"

            await send(ctx, msg)
        except Exception as e:
            await send(ctx, f"error fetching quote: ```{e}```")
    
    @commands.hybrid_command(help="Get oil prices")
    async def oil(self, ctx):
        try:
            await defer(ctx)
            res = requests.get("https://api.dungewar.com/oil-full").json().get('data', {})
            price = res.get('price')
            change = res.get('changes', {}).get('24h', {}).get('percent')
            comment = res.get('comment')
            meme = res.get('meme')
            meme_url = meme.get('url') if isinstance(meme, dict) else meme

            diff_content = f"${price} per barrel\n{'+' if change is not None and change >= 0 else ''}{change}% in the last 24 hours" if change is not None else f"${price} per barrel"
            content = f"```diff\n{diff_content}```"

            if comment:
                comment_lines = "\n".join(f"> *{line}*" if line.strip() else ">" for line in comment.strip().splitlines())
                content += f"\n{comment_lines}"

            content += "\n-# (source: [Dungewar API](<https://api.dungewar.com/oil-full>))"

            if meme_url:
                content += f"[.]({meme_url})"

            await send(ctx, content)
        except Exception as e:
            await send(ctx, f"error fetching oil prices: ```{e}```")

async def setup(bot: commands.Bot):
    await bot.add_cog(Dungewar(bot))
