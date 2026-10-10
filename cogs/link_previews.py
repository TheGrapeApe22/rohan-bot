import asyncio
import os
from datetime import date, timedelta
from typing import Literal
from urllib.parse import urlencode

import discord
from discord.ext import commands

import time
import json

class LinkPreviews(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(help="generate a funny website preview with a different redirect")
    async def breaking_news(self, ctx, title: str=None, description: str=None, image: str=None, message_text: str=None, provider: str=None, author: str=None, large_image: bool=None, is_video: bool=None, color: int=None, template: Literal['NYTimes', 'AP News', 'Prospector', 'BBC', 'None']='None'):
        data = {k: v for k, v in locals().items() if k not in ['ctx', 'self', 'template'] and v is not None}

        # load templates
        with open('data/article_templates.json', 'r') as f:
            templates = json.load(f)        
        for k, v in templates[template].items():
            if k not in data:
                data[k] = v
                # print(f"Setting {k} to {v}")

        if title:
            title_in_url = title.lower().replace(' ', '-')
            title_in_url = ''.join(c for c in title_in_url if c.isalnum() or c == '-')
            title_in_url = title_in_url or 'index'
        else:
            title_in_url = 'index'
        data['message_text'] = data['message_text'].replace('[date]', (date.today() - timedelta(days=1)).strftime("%Y/%m/%d"))
        data['message_text'] = data['message_text'].replace('[title_in_url]', title_in_url)

        # build output
        appear = data['message_text'].replace('http', 'htt￴p')
        previewed_url = os.getenv('PREVIEWED_URL').removesuffix('/') + '/?'
        previewed_url += urlencode(data)
        
        out = f'[{appear}](<https://discord.com/vanityurl/dotcom/steakpants/flour/flower/index11.html>)'
        out += f'[￴]({previewed_url})'

        if len(out) > 2000:
            await ctx.send(f"Message ({len(out)} characters) too long to send.")
        else:
            await ctx.send(out, allowed_mentions=discord.AllowedMentions.none())

    @commands.hybrid_command(help="convert link to rickroll link (note: fails if the url redirects)")
    async def rickroll(self, ctx, link: str, output: Literal['link', 'breaking_news command'] = 'link'):
        try:
            embed = await self.fetch(link)
            params = {
                'message_text': link,
                'title': embed.title,
                'description': embed.description,
                'image': embed.thumbnail.url if embed.thumbnail else embed.image.url if embed.image else None,
                'provider': embed.provider.name if embed.provider else None,
                'author': embed.author.name if embed.author else None,
                'large_image': embed.type in ['article', 'rich'] or None,
                'is_video': embed.type == 'video' or None,
                'color': embed.color
            }
            
            if output == 'link':
                await self.breaking_news(ctx, **params)
            else:
                await ctx.send(f'```/breaking_news {
                    ' '.join([f"{k}: {v}" for k, v in params.items() if v is not None])
                }```')

        except Exception as e:
            await ctx.send(f"Error: {e}")

    async def fetch(self, url) -> discord.Embed:
        channel = self.bot.get_channel(int(os.getenv('EMBED_CHANNEL_ID')))
        message = await channel.send(url)
        if message.embeds:
            return message.embeds[0]

        start_time = time.time()
        while True:
            if time.time() - start_time > 7:
                break

            # print("fetching...")
            message: discord.Message = await channel.fetch_message(message.id)
            if message.embeds:
                return message.embeds[0]

            await asyncio.sleep(1)

    @commands.hybrid_command()
    async def embeds(self, ctx, url):
        """Preview the embed for a given URL."""
        embed = await self.fetch(url)
        await ctx.send(json.dumps(embed.to_dict(), indent=4))

    @commands.hybrid_command()
    async def testembed(self, ctx):
        embed = discord.Embed.from_dict({
            "title": "Test",
            "description": "Testing author + provider",
            "author": {
                "name": "author"
            },
            "provider": {
                "name": "provider"
            }
        })
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LinkPreviews(bot))
