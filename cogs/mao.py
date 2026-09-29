import random

from utils.soliloquy import construct_abomination, seven_bag
from pathlib import Path
import json
import discord
from discord.ext import commands
from typing import Literal

def pluralize(count):
    return '' if count == 1 else 's'

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
            json.dump(cards, f, indent=4)
        await ctx.send(f"{reason}{'\n' if reason else ''}{user.mention if ping else user.name} now has {cards[user_id]} card{pluralize(cards[user_id])}.")
    @commands.hybrid_command(help="check how many cards a user has")
    async def get_card_count(self, ctx, user: discord.User, ping: bool = True):
        with open("cards.json", "r") as f:
            cards = json.load(f)
        user_id = str(user.id)
        count = cards.get(user_id, 0)
        await ctx.send(f"{user.mention if ping else user.name} has {count} card{pluralize(count)}.")
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
            leaderboard_text += f"{user.name}: {count} card{pluralize(count)}\n"
        await ctx.send(f"# Card Leaderboard\n{leaderboard_text}")

    # soliloquy
    @commands.hybrid_command(help="generate a soliloquy from inside jokes/copypastas")
    async def schizo_soliloquy(self, ctx, length: discord.app_commands.Range[int, 1, 25] = 1, include_image: bool = False):
        if ctx.author.id == 335921289900589066: # mason
            roll = random.randint(1, 6)
            if roll == 6:
                await ctx.send('frick you mason. you rolled a d6 and landed on a 6.')
            else:
                await ctx.send(f'frick you mason. you rolled a d6 and landed on a {roll}. roll a 6 to receive your soliloquy.')
                return

        file = None
        if include_image:
            file = discord.File(self.soliloquy_images.get_item())

        message = construct_abomination(length)
        if len(message) > 1984: # for the memes
            await ctx.send(f"Message ({len(message)} characters) too long to send. Try a shorter length.")
        await ctx.send(message, file=file)

    @commands.hybrid_command(help="translate a message to a programming language")
    async def translate(self, ctx, message: str, language: Literal['C++ (🧀)', 'Java']):
        if len(message) > 1000:
            await ctx.send(f"Message ({len(message)} characters) too long.")

        if ctx.author.id == 767458854249824328: # sharvil
            roll = random.randint(1, 6)
            if roll == 6:
                await ctx.send('frick you sharvil. you rolled a d6 and landed on a 6.')
            else:
                await ctx.send(f'frick you sharvil. you rolled a d6 and landed on a {roll}. roll a 6 to get your message translated.')
                return

        # sanitize message
        quotes = 0
        added_backslash = False
        i = 0
        while i < len(message):
            if message[i] == '"':
                quotes += 1
                message = message[:i] + '\\' + message[i:]
                i+=1
            if message[i] == '\\':
                if i == len(message) - 1:
                    message += '\\'
                    added_backslash = True
                    break
                i+=1
            i+=1

        prefix = ""
        if quotes > 0:
            prefix += f"Added backslash before {quotes} unescaped double-quote{pluralize(quotes)}. "
        if added_backslash:
            prefix += "Added backslash to end of message to prevent escaping the end quote."
        if prefix:
            prefix = '-# ' + prefix + '\n'
        
        message = message.replace('`', '`​')

        # translate
        if language == 'C++ (🧀)':
            await ctx.send(f"{prefix}```cpp\n#include <iostream>\n#define cheese int\n#define Cheese main\n#define cHeese (\n#define CHeese )\n#define chEese {{\n#define ChEese std\n#define cHEese ::\n#define CHEese cout\n#define cheEse <<\n#define CheEse \"{message}\"\n#define cHeEse endl\n#define CHeEse ;\n#define chEEse }}\n\ncheese Cheese cHeese CHeese chEese\n    ChEese cHEese CHEese cheEse CheEse cheEse ChEese cHEese cHeEse CHeEse\nchEEse\n```")
        elif language == 'Java':
            await ctx.send(f'{prefix}```java\nclass sentence {{\n  public static void main(String[] args) {{\n    System.out.println("{message}");\n  }}\n}}\n```')

    @commands.hybrid_command(help="add a line to david guoggins pretrained transformer gpt")
    async def add_gpt_line(self, ctx, line: str, source:str=''):
        if len(line) > 1900:
            await ctx.send(f"aborted; too long.")
            return
        with open('david_lines.json', 'r') as f:
            lines = json.load(f)
        with open('david_lines.json', 'w') as f:
            for line in lines:
                if line['line'] == line:
                    await ctx.send(f"Line already exists.")
                    return
            lines.append({'cited_by': ctx.author.id, 'line': line, 'source': source})
            json.dump(lines, f)
        await ctx.send(f'Added line to Guoggins Pretrained Transformer:\n`{line}`')

    @commands.hybrid_command(help="list all lines from david guoggins pretrained transformer gpt")
    async def list_gpt_lines(self, ctx):
        with open('david_lines.json', 'r') as f:
            lines = json.load(f)
        if not lines:
            await ctx.send("No lines found.")
            return
        output = str(json.dumps(lines))
        await ctx.send(f"{(output[0:1900] + '...') if len(output) > 1900 else output}")

    @commands.hybrid_command(help="generate/get a line from david guoggins pretrained transformer gpt")
    async def guoggins_pretrained_transformer(self, ctx):
        with open('david_lines.json', 'r') as f:
            lines = json.load(f)
        if not lines:
            await ctx.send("No lines found.")
            return
        
        line_object = random.choice(lines)
        line_text = line_object["line"].replace("\\n", "\n> ")
        source_line = f'\n-# source: {line_object["source"]}' if line_object["source"] else ''

        await ctx.send(f'*Guoggins Pretrained Transformer:*\n> {line_text}{source_line}')


async def setup(bot: commands.Bot):
    await bot.add_cog(Mao(bot))
