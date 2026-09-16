import asyncio
import os
from datetime import date, timedelta
from typing import Literal
from urllib.parse import quote_plus

import discord
from discord.ext import commands

from utils.chromium_session import ChromiumSession

class LinkPreviews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(help="generate a funny website preview with a different redirect")
    async def breaking_news(self, ctx, title: str=None, description: str=None, image_url: str=None, message_text: str=None, provider: str=None, author: str=None, large_image: bool=True, template: Literal['NYTimes', 'AP News', 'Prospector', 'BBC', 'None']='None'):
        destination_url = 'https://discord.com/vanityurl/dotcom/steakpants/flour/flower/index11.html' # no making this a parameter, because abusable

        def cleaned(value: str | None) -> str:
            return quote_plus(value or '', safe='')

        if title:
            title_in_url = title.lower().replace(' ', '-')
            title_in_url = ''.join(c for c in title_in_url if c.isalnum() or c == '-')
            title_in_url = title_in_url or 'index'
        else:
            title_in_url = 'index'

        if template == 'NYTimes':
            yesterday = date.today() - timedelta(days=1)
            message_text = message_text or f'https://www.nytimes.com/{yesterday.strftime("%Y/%m/%d")}/politics/{title_in_url}.html'
            provider = provider or 'The New York Times'
            author = author or 'By Mike Isaac'
            image_url = image_url or 'https://static01.nyt.com/newsgraphics/images/icons/defaultPromoCrop.png'
            large_image = True
        elif template == 'AP News':
            message_text = message_text or f'https://apnews.com/article/{title_in_url}-d2d1bac8e8666c681937665596a4f603'
            provider = provider or 'AP News'
            author = author or 'World News'
            image_url = image_url or 'https://static01.nyt.com/newsgraphics/images/icons/defaultPromoCrop.png'
            large_image = False
        elif template == 'BBC':
            message_text = message_text or f'https://www.bbc.com/news/articles/ce8767g4jdpo'
            provider = provider or 'BBC News'
            author = author or 'By Mark Elliot'
            image_url = image_url or 'https://static.wikia.nocookie.net/logopedia/images/b/ba/BBC_News_2019_%28Black_box%29.svg/revision/latest/scale-to-width-down/250?cb=20211024233853'
            large_image = False
        elif template == 'Prospector':
            message_text = message_text or f'https://prospector.com/11608/news/{title_in_url}'
            provider = provider or 'The Prospector'
            image_url = image_url or 'https://chsprospector.com/wp-content/uploads/2025/08/prospector-masthead-enhanced.png'
            large_image = True
        else:
            message_text = message_text or "cheese"

        first = True
        def conj():
            nonlocal first
            if first:
                first = False
                return '/?'
            else:
                return '&'
    
        previewed_url = os.getenv('PREVIEWED_URL')
        if title:
            previewed_url += f'{conj()}title={cleaned(title) or ""}'
        if description:
            previewed_url += f'{conj()}description={cleaned(description)}'
        if image_url:
            previewed_url += f'{conj()}image={cleaned(image_url)}'
        if provider:
            previewed_url += f'{conj()}provider_name={cleaned(provider)}'
        if author:
            previewed_url += f'{conj()}author_name={cleaned(author)}'
        previewed_url += f'{conj()}author_url={cleaned(destination_url)}'
        previewed_url += f'{conj()}provider_url={cleaned(destination_url)}'
        previewed_url += f'{conj()}appear_url={cleaned(message_text)}'
        previewed_url += f'{conj()}large_image={str(large_image).lower()}'

        out = ''
        if '//' in message_text:
            sep = message_text.find('//') + 2
            out += f'[{message_text[:sep]}](<{destination_url}>)'
        else:
            sep = 0
        if len(message_text) > 1:
            out += f'[{message_text[sep:-1]}](<{destination_url}>)'
        out += f'[{message_text[-1]}]({previewed_url})'

        if len(out) > 2000:
            await ctx.send(f"Message ({len(out)} characters) too long to send.")
        else:
            await ctx.send(out, allowed_mentions=discord.AllowedMentions.none())

    @commands.hybrid_command(help="convert link to rickroll link (note: fails if the url redirects)")
    async def rickroll(self, ctx, link: str, output: Literal['link', 'breaking_news command'] = 'link', code_blocks: bool = True):
        try:
            async with await ChromiumSession.create() as session:
                res = await session.get_metadata(link)
                # print(res)
                if output == 'link':
                    # await self.breaking_news(
                    #     ctx,
                    #     title=res['title'],
                    #     description=res['description'],
                    #     image_url=res['image_url'],
                    #     message_text=link,
                    #     provider=res['provider'],
                    #     author=res['author'],
                    #     large_image=res['large_image'],
                    #     template='None'
                    # )
                    
                    await self.breaking_news(
                        ctx,
                        **{k: res[k] for k in res.keys() if res[k] is not None},
                        message_text=link,
                        template='None'
                    )
                else:
                    # send the slash command as a literal
                    out = '/breaking_news'
                    out += f' message_text: {link}'
                    for k in res.keys():
                        if res[k] is not None:
                            param = res[k]
                            if k == 'description' and len(param) > 500:
                                param = param[:500] + '...'
                            elif k == 'image_url' and res[k][0] == '/':
                                base_url = link.split('/')[0] + '//' + link.split('/')[2]
                                param = f'{base_url}{res[k]}'
                            out += f' {k}: {param}'
                    if code_blocks:
                        out = f'```\n{out}```'
                    await ctx.send(out)

        except Exception as e:
            await ctx.send(f"Error: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(LinkPreviews(bot))
