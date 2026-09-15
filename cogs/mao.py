import random
import os
from datetime import date, timedelta

from soliloquy import construct_abomination, seven_bag
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
            json.dump(cards, f)
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

    @commands.hybrid_command(help="generate a funny website preview with a different redirect")
    async def breaking_news(self, ctx, title: str, description: str='', image_url: str='', message_text: str='', provider: str='', author: str='', large_image: bool=True, encode_characters: bool=False, template: Literal['NYTimes', 'AP News', 'Prospector', 'BBC', 'None']='NYTimes'):
        destination_url = 'https://discord.com/vanityurl/dotcom/steakpants/flour/flower/index11.html' # no making this a parameter, because abusable

        def cleaned(s: str) -> str:
            replacements = {
                '+': '%2B',
                '%': '%25',
                '&': '%26',
                '?': '%3F',
                '=': '%3D',
                '/': '%2F',
                '.': '%2E',
                ',': '%2C',
                '(': '%28',
                ')': '%29',
                ':': '%3A',
                ';': '%3B',
                "'": '%27',
                '$': '%24',
                '"': '%22',
            }
            if encode_characters:
                for old, new in replacements.items():
                    s = s.replace(old, new)
            s = s.replace(' ', '+')
            return s

        if not message_text:
            yesterday = date.today() - timedelta(days=1)
            cleaned_title = title.lower().replace(" ", "-")
            cleaned_title = ''.join(c for c in cleaned_title if c.isalnum() or c == '-')
            if template == 'NYTimes':
                message_text = message_text or f'https://www.nytimes.com/{yesterday.strftime("%Y/%m/%d")}/politics/{cleaned_title}.html'
                provider = provider or 'The New York Times'
                author = author or 'By Mike Isaac'
                preview_image_url = preview_image_url or 'https://static01.nyt.com/newsgraphics/images/icons/defaultPromoCrop.png'
                large_image = True
            elif template == 'AP News':
                message_text = message_text or f'https://apnews.com/article/{cleaned_title}-d2d1bac8e8666c681937665596a4f603'
                provider = provider or 'The New York Times'
                author = author or 'By Mike Isaac'
                preview_image_url = preview_image_url or 'https://static01.nyt.com/newsgraphics/images/icons/defaultPromoCrop.png'
                large_image = False
            elif template == 'BBC':
                message_text = message_text or f'https://www.bbc.com/news/articles/ce8767g4jdpo'
                provider = provider or 'BBC News'
                author = author or 'By Mark Elliot'
                preview_image_url = preview_image_url or 'https://static.wikia.nocookie.net/logopedia/images/b/ba/BBC_News_2019_%28Black_box%29.svg/revision/latest/scale-to-width-down/250?cb=20211024233853'
                large_image = False
            elif template == 'Prospector':
                message_text = message_text or f'https://prospector.com/11608/news/{cleaned_title}'
                provider = provider or 'The Prospector'
                preview_image_url = preview_image_url or 'https://chsprospector.com/wp-content/uploads/2025/08/prospector-masthead-enhanced.png'
                large_image = True

        previewed_url = os.getenv('PREVIEWED_URL')
        previewed_url += f'?title={cleaned(title)}'
        if description:
            previewed_url += f'&description={cleaned(description)}'
        if image_url:
            previewed_url += f'&image={cleaned(image_url)}'
        if provider:
            previewed_url += f'&provider_name={cleaned(provider)}'
        if author:
            previewed_url += f'&author_name={cleaned(author)}'
        previewed_url += f'&author_url={cleaned(destination_url)}'
        previewed_url += f'&provider_url={cleaned(destination_url)}'
        previewed_url += f'&appear_url={cleaned(message_text)}'
        previewed_url += f'&large_image={str(large_image).lower()}'

        out = ''
        if '//' in message_text:
            sep = message_text.find('//') + 2
            out += f'[{message_text[:sep]}](<{destination_url}>)'
        else:
            sep = 0
        out += f'[{message_text[sep:-1]}](<{destination_url}>)'
        out += f'[{message_text[-1]}]({previewed_url})'
        
        await ctx.send(out)

async def setup(bot: commands.Bot):
    await bot.add_cog(Mao(bot))
