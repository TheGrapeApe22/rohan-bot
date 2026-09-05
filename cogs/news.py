import discord
from discord.ext import commands
from typing import Optional, Literal, List, Dict, Any
import aiohttp
import asyncio
import re
from datetime import datetime

BASE_URL = "https://api.dungewar.com/bsb-news"


def parse_iso_time(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 timestamp string from the API."""
    if not ts_str:
        return None
    try:
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except Exception:
        return None


def extract_headlines(text: str) -> List[str]:
    """Extract clean section headers and top-level headline bullets from markdown text."""
    headlines: List[str] = []
    lines = text.splitlines()
    for line in lines:
        raw_line = line
        stripped = line.strip()
        if not stripped or stripped.startswith("---"):
            continue

        # Markdown section headers (# Header or ## Header)
        if stripped.startswith("#"):
            clean_heading = stripped.lstrip("#").strip()
            if clean_heading:
                headlines.append(f"\n### 📂 {clean_heading}")
        # Top-level bold bullet item (- **Title**: ...)
        elif re.match(r"^\s*[-*•]\s*\*\*(.*?)\*\*", raw_line) and not raw_line.startswith(("    ", "\t", "  ")):
            m = re.search(r"^\s*[-*•]\s*\*\*(.*?)\*\*", raw_line)
            if m:
                title = m.group(1).strip().rstrip(":")
                headlines.append(f"• **{title}**")
        # Top-level labeled bullet (- Title: ...)
        elif re.match(r"^\s*[-*•]\s+([A-Z0-9].*?:)", raw_line) and not raw_line.startswith(("    ", "\t", "  ")):
            m = re.search(r"^\s*[-*•]\s+([A-Z0-9].*?):", raw_line)
            if m:
                title = m.group(1).strip().rstrip(":")
                headlines.append(f"• **{title}**")

    return headlines


def split_text_to_pages(text: str, max_chars: int = 3500) -> List[str]:
    """Split markdown text into readable pages within Discord embed description limits."""
    if len(text) <= max_chars:
        return [text]

    pages: List[str] = []
    sections = text.split("\n---\n")
    current_page = ""

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) > max_chars:
            paragraphs = sec.split("\n\n")
            for p in paragraphs:
                if len(current_page) + len(p) + 2 > max_chars and current_page:
                    pages.append(current_page.strip())
                    current_page = p
                else:
                    current_page = (current_page + "\n\n" + p).strip() if current_page else p
        else:
            if len(current_page) + len(sec) + 5 > max_chars and current_page:
                pages.append(current_page.strip())
                current_page = sec
            else:
                current_page = (current_page + "\n\n---\n\n" + sec).strip() if current_page else sec

    if current_page:
        pages.append(current_page.strip())

    return pages if pages else [text]


def build_story_embed(
    story: Dict[str, Any],
    page_idx: int = 0,
    headlines_mode: bool = False,
    story_idx: int = 0,
    total_stories: int = 1
) -> discord.Embed:
    """Build a rich, clean Discord Embed for a news story."""
    story_id = story.get("id", "?")
    title = story.get("title")
    text = story.get("text") or story.get("content") or ""
    author = story.get("author")
    tags = story.get("tags")
    created_at = story.get("createdAt") or story.get("timestamp")
    dt = parse_iso_time(created_at)

    time_str = f"<t:{int(dt.timestamp())}:R>" if dt else "Recently"
    story_url = f"{BASE_URL}/{story_id}"

    if headlines_mode:
        embed_title = f"📑 BSB News Headlines • Story #{story_id}" if not title else f"📑 {title} (Headlines)"
        embed = discord.Embed(
            title=embed_title,
            color=0x10B981,  # Emerald Green
            url=story_url
        )
        headlines = extract_headlines(text)
        if not headlines and title:
            headlines = [f"• **{title}**"]
        elif not headlines:
            first_line = text.strip().split("\n")[0] if text else "No content available."
            headlines = [f"• {first_line[:200]}"]

        header_meta = f"-# 📅 Published {time_str} • Story ID: `#{story_id}`"
        desc = f"{header_meta}\n" + "\n".join(headlines)
        if len(desc) > 4000:
            desc = desc[:3990] + "..."
        embed.description = desc

        footer_parts = []
        if total_stories > 1:
            footer_parts.append(f"Story {story_idx + 1}/{total_stories}")
        footer_parts.append("BSB News • Dungewar Network")
        embed.set_footer(text=" • ".join(footer_parts))
    else:
        pages = split_text_to_pages(text)
        total_pages = len(pages)
        page_idx = max(0, min(page_idx, total_pages - 1))
        content = pages[page_idx] if pages else "(No content available)"

        embed_title = f"📰 BSB News • Story #{story_id}" if not title else f"📰 {title}"
        embed = discord.Embed(
            title=embed_title,
            color=0x3B82F6,  # Royal Blue
            url=story_url
        )

        header_meta = f"-# 📅 Published {time_str} • Story ID: `#{story_id}`"
        if author:
            header_meta += f" • ✍️ {author}"
        if tags and isinstance(tags, list):
            tags_str = ", ".join(str(t) for t in tags)
            header_meta += f" • 🏷️ {tags_str}"

        full_desc = f"{header_meta}\n\n{content}"
        if len(full_desc) > 4096:
            full_desc = full_desc[:4090] + "..."
        embed.description = full_desc

        footer_parts = []
        if total_stories > 1:
            footer_parts.append(f"Story {story_idx + 1}/{total_stories}")
        if total_pages > 1:
            footer_parts.append(f"Page {page_idx + 1}/{total_pages}")
        footer_parts.append("BSB News • Dungewar Network")
        embed.set_footer(text=" • ".join(footer_parts))

    if dt:
        embed.timestamp = dt

    return embed


class NewsView(discord.ui.View):
    """Interactive Discord UI View with stable buttons for pagination, mode toggle, and random stories."""

    def __init__(
        self,
        cog: "News",
        stories: List[Dict[str, Any]],
        initial_headlines: bool = False,
        timeout: float = 600.0
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.stories = stories
        self.story_idx = 0
        self.page_idx = 0
        self.headlines_mode = initial_headlines
        self.message: Optional[discord.Message] = None

        # Link button added once to the view
        story_id = self.current_story.get("id")
        link_url = f"{BASE_URL}/{story_id}" if story_id else BASE_URL
        self.url_btn = discord.ui.Button(
            label="🌐 API Source",
            style=discord.ButtonStyle.link,
            url=link_url
        )
        self.add_item(self.url_btn)

        self.update_buttons()

    @property
    def current_story(self) -> Dict[str, Any]:
        if 0 <= self.story_idx < len(self.stories):
            return self.stories[self.story_idx]
        return {}

    @property
    def current_pages(self) -> List[str]:
        text = self.current_story.get("text") or self.current_story.get("content") or ""
        return split_text_to_pages(text)

    def update_buttons(self):
        """Update button enabled states and labels safely without destroying components."""
        total_pages = len(self.current_pages) if not self.headlines_mode else 1
        can_go_prev = (self.page_idx > 0) or (self.story_idx > 0)
        can_go_next = (self.page_idx < total_pages - 1) or (self.story_idx < len(self.stories) - 1)

        self.btn_prev.disabled = not can_go_prev
        self.btn_next.disabled = not can_go_next
        self.btn_toggle.label = "📰 Full Text" if self.headlines_mode else "📑 Headlines"

        story_id = self.current_story.get("id")
        self.url_btn.url = f"{BASE_URL}/{story_id}" if story_id else BASE_URL

    def get_current_embed(self) -> discord.Embed:
        return build_story_embed(
            story=self.current_story,
            page_idx=self.page_idx,
            headlines_mode=self.headlines_mode,
            story_idx=self.story_idx,
            total_stories=len(self.stories)
        )

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.headlines_mode and self.page_idx > 0:
            self.page_idx -= 1
        elif self.story_idx > 0:
            self.story_idx -= 1
            if not self.headlines_mode:
                self.page_idx = len(self.current_pages) - 1
            else:
                self.page_idx = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_pages = len(self.current_pages) if not self.headlines_mode else 1
        if not self.headlines_mode and self.page_idx < total_pages - 1:
            self.page_idx += 1
        elif self.story_idx < len(self.stories) - 1:
            self.story_idx += 1
            self.page_idx = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    @discord.ui.button(label="📑 Headlines", style=discord.ButtonStyle.primary)
    async def btn_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.headlines_mode = not self.headlines_mode
        self.page_idx = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_current_embed(), view=self)

    @discord.ui.button(label="🎲 Random", style=discord.ButtonStyle.secondary)
    async def btn_random(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        story = await self.cog.fetch_random_story()
        if story:
            self.stories = [story]
            self.story_idx = 0
            self.page_idx = 0
            self.update_buttons()
            await interaction.edit_original_response(embed=self.get_current_embed(), view=self)
        else:
            await interaction.followup.send("Could not fetch a random story at this time.", ephemeral=True)

    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.style != discord.ButtonStyle.link:
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class News(commands.Cog, name="News"):
    """BSB News commands for fetching latest news, headlines, searching, and browsing stories."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10.0)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def cog_unload(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def fetch_latest_story(self) -> Optional[Dict[str, Any]]:
        session = await self.get_session()
        try:
            async with session.get(f"{BASE_URL}/latest") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data")
        except Exception as e:
            print(f"[News Cog] Error fetching latest story: {e}")
        return None

    async def fetch_random_story(self) -> Optional[Dict[str, Any]]:
        session = await self.get_session()
        try:
            async with session.get(f"{BASE_URL}/random") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data")
        except Exception as e:
            print(f"[News Cog] Error fetching random story: {e}")
        return None

    async def fetch_story_by_id(self, story_id: int) -> Optional[Dict[str, Any]]:
        session = await self.get_session()
        try:
            async with session.get(f"{BASE_URL}/{story_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data")
        except Exception as e:
            print(f"[News Cog] Error fetching story #{story_id}: {e}")
        return None

    async def fetch_news_list(
        self,
        sort: str = "newest",
        limit: int = 5,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        session = await self.get_session()
        params: Dict[str, Any] = {"sort": sort, "limit": limit}
        if query:
            params["q"] = query
        try:
            async with session.get(BASE_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("data", [])
        except Exception as e:
            print(f"[News Cog] Error fetching news list: {e}")
        return []

    async def _send_story_view(
        self,
        ctx: commands.Context,
        stories: List[Dict[str, Any]],
        headlines_mode: bool = False
    ):
        if not stories:
            embed = discord.Embed(
                title="🔍 No News Stories Found",
                description="No matching news stories were found. Try another search keyword or run `/news` for the latest update.",
                color=0xF59E0B
            )
            await ctx.send(embed=embed)
            return

        view = NewsView(self, stories, initial_headlines=headlines_mode)
        embed = view.get_current_embed()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # Hybrid Command Group: /news and .news
    @commands.hybrid_group(
        name="news",
        fallback="latest",
        help="Fetch BSB news stories. Usage: `/news` or `.news [query|id|random|headlines]`"
    )
    @discord.app_commands.describe(
        query_or_id="Optional story ID (e.g. 2), search keyword, or mode (random, headlines)",
        headlines_only="Show concise headlines instead of full story text",
        sort="Sort order for stories (newest or oldest)"
    )
    async def news_group(
        self,
        ctx: commands.Context,
        query_or_id: Optional[str] = None,
        headlines_only: bool = False,
        sort: Literal["newest", "oldest"] = "newest"
    ):
        """Fetch news stories with flexible parameters."""
        if query_or_id is not None:
            clean_arg = query_or_id.strip()
            # If numeric ID provided: e.g. .news 2
            if clean_arg.isdigit():
                story = await self.fetch_story_by_id(int(clean_arg))
                if not story:
                    embed = discord.Embed(
                        title="❌ Story Not Found",
                        description=f"News story with ID **#{clean_arg}** was not found.",
                        color=0xEF4444
                    )
                    await ctx.send(embed=embed)
                    return
                await self._send_story_view(ctx, [story], headlines_mode=headlines_only)
                return
            # If 'random' requested
            if clean_arg.lower() in ("random", "rand", "r"):
                story = await self.fetch_random_story()
                if not story:
                    await ctx.send("❌ Unable to fetch random story.")
                    return
                await self._send_story_view(ctx, [story], headlines_mode=headlines_only)
                return
            # If 'headlines' requested
            if clean_arg.lower() in ("headlines", "headline", "hl"):
                stories = await self.fetch_news_list(sort=sort, limit=5)
                await self._send_story_view(ctx, stories, headlines_mode=True)
                return
            # Otherwise treat as keyword search
            stories = await self.fetch_news_list(sort=sort, limit=5, query=clean_arg)
            await self._send_story_view(ctx, stories, headlines_mode=headlines_only)
            return

        # Default fallback: fetch latest story
        if sort == "oldest":
            stories = await self.fetch_news_list(sort="oldest", limit=1)
            story = stories[0] if stories else None
        else:
            story = await self.fetch_latest_story()

        if not story:
            embed = discord.Embed(
                title="⚠️ No News Available",
                description="Unable to fetch news from BSB News API (`api.dungewar.com/bsb-news`). Please try again later.",
                color=0xEF4444
            )
            await ctx.send(embed=embed)
            return

        await self._send_story_view(ctx, [story], headlines_mode=headlines_only)

    @news_group.command(name="random", help="Fetch a random BSB news story.")
    @discord.app_commands.describe(headlines_only="Show concise headlines instead of full text")
    async def news_random(self, ctx: commands.Context, headlines_only: bool = False):
        """Fetch a random story from BSB news."""
        story = await self.fetch_random_story()
        if not story:
            embed = discord.Embed(
                title="⚠️ Error",
                description="Unable to fetch a random story at this time.",
                color=0xEF4444
            )
            await ctx.send(embed=embed)
            return
        await self._send_story_view(ctx, [story], headlines_mode=headlines_only)

    @news_group.command(name="search", help="Search BSB news stories by keyword.")
    @discord.app_commands.describe(
        query="Keyword or phrase to search for",
        headlines_only="Show concise headlines instead of full text",
        sort="Sort order (newest or oldest)",
        limit="Maximum number of stories to fetch (1-5)"
    )
    async def news_search(
        self,
        ctx: commands.Context,
        query: str,
        headlines_only: bool = False,
        sort: Literal["newest", "oldest"] = "newest",
        limit: commands.Range[int, 1, 5] = 5
    ):
        """Search stories by keyword."""
        stories = await self.fetch_news_list(sort=sort, limit=int(limit), query=query)
        await self._send_story_view(ctx, stories, headlines_mode=headlines_only)

    @news_group.command(name="id", help="Fetch a specific BSB news story by numeric ID.")
    @discord.app_commands.describe(
        story_id="Numeric ID of the story",
        headlines_only="Show concise headlines instead of full text"
    )
    async def news_id(self, ctx: commands.Context, story_id: int, headlines_only: bool = False):
        """Fetch a story by numeric ID."""
        story = await self.fetch_story_by_id(story_id)
        if not story:
            embed = discord.Embed(
                title="❌ Story Not Found",
                description=f"News story with ID **#{story_id}** was not found.",
                color=0xEF4444
            )
            await ctx.send(embed=embed)
            return
        await self._send_story_view(ctx, [story], headlines_mode=headlines_only)

    @news_group.command(name="headlines", help="Show headline summaries of recent news stories.")
    @discord.app_commands.describe(
        query="Optional keyword to filter headlines",
        sort="Sort order (newest or oldest)",
        limit="Number of stories to include (1-5)"
    )
    async def news_headlines(
        self,
        ctx: commands.Context,
        query: Optional[str] = None,
        sort: Literal["newest", "oldest"] = "newest",
        limit: commands.Range[int, 1, 5] = 5
    ):
        """View headlines overview directly."""
        stories = await self.fetch_news_list(sort=sort, limit=int(limit), query=query)
        await self._send_story_view(ctx, stories, headlines_mode=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(News(bot))
