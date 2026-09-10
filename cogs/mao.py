from soliloquy import construct_abomination, seven_bag
from pathlib import Path
import json
import discord
from discord.ext import commands
from typing import Literal

class Mao(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.folder_path = Path("assets/soliloquy/attachments")
        self.soliloquy_images = seven_bag([f'{self.folder_path}/{f.name}' for f in self.folder_path.iterdir()])

    # mao rules
    @commands.hybrid_command(help="increment a card count for a user, as a consequence for breaking a Mao rule")
    async def give_card(self, ctx, user: discord.User, reason: str = '', ping: bool = True):
        with open("cards.json", "r") as f:
            cards = json.load(f)
        user_id = str(user.id)
        if user_id not in cards:
            cards[user_id] = 0
        cards[user_id] += 1
        with open("cards.json", "w") as f:
            json.dump(cards, f)
        await ctx.send(f"{reason}{'\n' if reason else ''}{user.mention if ping else user.name} now has {cards[user_id]} card{'' if cards[user_id] == 1 else 's'}.")
    @commands.hybrid_command(help="check how many cards a user has")
    async def get_card_count(self, ctx, user: discord.User, ping: bool = True):
        with open("cards.json", "r") as f:
            cards = json.load(f)
        user_id = str(user.id)
        count = cards.get(user_id, 0)
        await ctx.send(f"{user.mention if ping else user.name} has {count} card{'' if count == 1 else 's'}.")
    @commands.hybrid_command(help="show the card counts for all users")
    async def leaderboard(self, ctx):
        with open("cards.json", "r") as f:
            cards = json.load(f)
        if not cards:
            await ctx.send("(empty)")
            return
        sorted_cards = sorted(cards.items(), key=lambda x: x[1], reverse=True)
        leaderboard_text = ''
        for user_id, count in sorted_cards:
            user = await self.bot.fetch_user(int(user_id))
            leaderboard_text += f"{user.name}: {count} card{'' if count == 1 else 's'}\n"
        await ctx.send(f"# Card Leaderboard\n{leaderboard_text}")

    # soliloquy
    @commands.hybrid_command(help="generate a soliloquy from inside jokes/copypastas")
    async def schizo_soliloquy(self, ctx, length: discord.app_commands.Range[int, 1, 25] = 1, include_image: bool = False):
        file = None
        if include_image:
            file = discord.File(self.soliloquy_images.get_item())

        message = construct_abomination(length)
        if len(message) > 1984: # for the memes
            await ctx.send(f"Message ({len(message)} characters) too long to send. Try a shorter length.")
        await ctx.send(message, file=file)

    # translate
    @commands.hybrid_command(help="translate a message to a programming language")
    async def translate(self, ctx, message: str, language: Literal['C++ (🧀)', 'Java']):
        if '"' in message or message[-1] == '\\':
            await ctx.send("Invalid message: cannot contain double quotes or end with a backslash.")
            return
        
        if language == 'C++ (🧀)':
            await ctx.send(f"```cpp\n#include <iostream>\n#define cheese int\n#define Cheese main\n#define cHeese (\n#define CHeese )\n#define chEese {{\n#define ChEese std\n#define cHEese ::\n#define CHEese cout\n#define cheEse <<\n#define CheEse \"{message}\"\n#define cHeEse endl\n#define CHeEse ;\n#define chEEse }}\n\ncheese Cheese cHeese CHeese chEese\n    ChEese cHEese CHEese cheEse CheEse cheEse ChEese cHEese cHeEse CHeEse\nchEEse\n```")
        elif language == 'Java':
            await ctx.send(f'```java\nclass sentence {{\n  public static void main(String[] args) {{\n    System.out.println("{message}");\n  }}\n}}\n```')

async def setup(bot: commands.Bot):
    await bot.add_cog(Mao(bot))
