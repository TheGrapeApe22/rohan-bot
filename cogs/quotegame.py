import discord
from discord.ext import commands
from typing import List, Tuple, Dict, Any, Optional
import aiohttp
import asyncio
import re
import random

API_URL = "https://api.dungewar.com/random-quote"
NUM_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]


def parse_quote_string(raw: str) -> Optional[Tuple[str, str]]:
    """Extract quote text and author from API string formatted as 'Quote text. (Author Name)'."""
    raw = raw.strip()
    # Match trailing (Author Name)
    m = re.search(r'^(.*)\s*\(([^()]+)\)\s*$', raw, re.DOTALL)
    if m:
        text = m.group(1).strip().strip('"').strip()
        author = m.group(2).strip()
        return text, author
    # Fallback to rfind
    if "(" in raw and raw.endswith(")"):
        idx = raw.rfind("(")
        text = raw[:idx].strip().strip('"').strip()
        author = raw[idx + 1:-1].strip()
        return text, author
    return None


class QuoteGameSession:
    """Manages the state and progress of a single minigame session with multi-user participation."""

    def __init__(self, quotes: List[Tuple[str, str]], initiator_name: str):
        self.quotes = quotes  # List of (text, correct_author)
        self.total = len(quotes)
        self.initiator_name = initiator_name
        self.current_idx = 0
        self.user_answers: List[Tuple[str, str]] = []  # List of (author_guess, player_name)
        self.participants: set = set()

        # Candidate authors (shuffled for display)
        self.candidate_authors = list(set(a for _, a in quotes))
        random.shuffle(self.candidate_authors)

    @property
    def is_finished(self) -> bool:
        return self.current_idx >= self.total

    @property
    def current_quote(self) -> Tuple[str, str]:
        if not self.is_finished:
            return self.quotes[self.current_idx]
        return ("", "")

    @property
    def score(self) -> int:
        correct = 0
        for i, (ans, _) in enumerate(self.user_answers):
            if i < len(self.quotes) and ans == self.quotes[i][1]:
                correct += 1
        return correct

    def submit_answer(self, author: str, player_name: str):
        self.user_answers.append((author, player_name))
        self.participants.add(player_name)
        self.current_idx += 1


def build_game_embed(session: QuoteGameSession) -> discord.Embed:
    """Build the embed for the active question state."""
    embed = discord.Embed(
        title="🧩 Quote Matching Minigame",
        color=0xF59E0B  # Amber
    )

    lines = [
        "Match each quote to the person who said it!\n*Anyone in the channel can click to guess!*\n",
        "**📜 Quotes to Match:**"
    ]

    for i, (text, _) in enumerate(session.quotes):
        emoji = NUM_EMOJIS[i] if i < len(NUM_EMOJIS) else f"[{i + 1}]"
        if i < len(session.user_answers):
            ans, p_name = session.user_answers[i]
            lines.append(f"{emoji} *\"{text}\"*\n   └ 👤 *Selected:* **{ans}** *(by {p_name})*")
        elif i == session.current_idx:
            lines.append(f"{emoji} *\"{text}\"*\n   └ ❓ *(Selecting now...)*")
        else:
            lines.append(f"{emoji} *\"{text}\"*\n   └ ⏳ *(Waiting...)*")

    lines.append("\n**👥 Candidate Authors:**")
    for author in session.candidate_authors:
        lines.append(f"• **{author}**")

    lines.append(f"\n👉 **Question {session.current_idx + 1} of {session.total}:** Who said Quote #{session.current_idx + 1}?")

    embed.description = "\n".join(lines)
    embed.set_footer(text=f"Match all {session.total} quotes! • Started by {session.initiator_name}")
    return embed


def build_results_embed(session: QuoteGameSession) -> discord.Embed:
    """Build the final score and recap embed."""
    score = session.score
    total = session.total
    pct = int((score / total) * 100) if total > 0 else 0

    if score == total:
        title = f"🎉 Perfect Score! ({score}/{total})"
        color = 0x10B981  # Emerald Green
    elif score > 0:
        title = f"👏 Good Effort! ({score}/{total})"
        color = 0x3B82F6  # Royal Blue
    else:
        title = f"😅 Better Luck Next Time! ({score}/{total})"
        color = 0xEF4444  # Red

    embed = discord.Embed(
        title=title,
        color=color
    )

    lines = [f"🎯 **Final Score: {score} / {total} ({pct}%)**\n"]

    for i, (text, correct_author) in enumerate(session.quotes):
        emoji = NUM_EMOJIS[i] if i < len(NUM_EMOJIS) else f"[{i + 1}]"
        user_ans, p_name = session.user_answers[i] if i < len(session.user_answers) else ("None", "Unknown")
        is_correct = (user_ans == correct_author)

        lines.append(f"{emoji} *\"{text}\"*")
        if is_correct:
            lines.append(f"   • Answer by {p_name}: **{user_ans}** ✅")
        else:
            lines.append(f"   • Answer by {p_name}: **{user_ans}** ❌\n   • Actual author: **{correct_author}**")
        lines.append("")

    players_str = ", ".join(session.participants) if session.participants else session.initiator_name
    lines.append(f"-# Played by {players_str} • api.dungewar.com/random-quote")
    embed.description = "\n".join(lines)
    return embed


class AuthorButton(discord.ui.Button):
    """Button representing one candidate author option."""

    def __init__(self, author: str, row: int = 0):
        label = author if len(author) <= 80 else author[:77] + "..."
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)
        self.author_name = author

    async def callback(self, interaction: discord.Interaction):
        view: QuoteGameView = self.view
        player_name = interaction.user.display_name
        view.session.submit_answer(self.author_name, player_name)

        if not view.session.is_finished:
            embed = build_game_embed(view.session)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            view.show_results_buttons()
            embed = build_results_embed(view.session)
            await interaction.response.edit_message(embed=embed, view=view)


class PlayAgainButton(discord.ui.Button):
    """Button to start another game round with fresh quotes."""

    def __init__(self):
        super().__init__(label="🔄 Play Again", style=discord.ButtonStyle.primary, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: QuoteGameView = self.view
        await interaction.response.defer()
        new_quotes = await view.cog.fetch_unique_quotes(view.session.total)
        if not new_quotes or len(new_quotes) < 2:
            await interaction.followup.send("⚠️ Unable to fetch new quotes from the API right now. Please try again.", ephemeral=True)
            return

        view.session = QuoteGameSession(
            quotes=new_quotes,
            initiator_name=interaction.user.display_name
        )
        view.setup_author_buttons()
        embed = build_game_embed(view.session)
        await interaction.edit_original_response(embed=embed, view=view)


class AuthorSelectMenu(discord.ui.Select):
    """Dropdown select menu for games with more than 5 authors."""

    def __init__(self, authors: List[str]):
        options = [
            discord.SelectOption(
                label=author[:100],
                value=author,
                description=f"Select {author[:50]}"
            )
            for author in authors
        ]
        super().__init__(placeholder="Choose the author...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        view: QuoteGameView = self.view
        player_name = interaction.user.display_name
        selected_author = self.values[0]
        view.session.submit_answer(selected_author, player_name)

        if not view.session.is_finished:
            embed = build_game_embed(view.session)
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            view.show_results_buttons()
            embed = build_results_embed(view.session)
            await interaction.response.edit_message(embed=embed, view=view)


class QuoteGameView(discord.ui.View):
    """Discord UI View managing author selection buttons and replay options."""

    def __init__(self, cog: "QuoteGame", session: QuoteGameSession, timeout: float = 300.0):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.session = session
        self.message: Optional[discord.Message] = None
        self.setup_author_buttons()

    def setup_author_buttons(self):
        """Populate the view with candidate author buttons or dropdown."""
        self.clear_items()
        authors = self.session.candidate_authors

        if len(authors) <= 5:
            for author in authors:
                self.add_item(AuthorButton(author, row=0))
        elif len(authors) <= 10:
            for i, author in enumerate(authors):
                row = 0 if i < 5 else 1
                self.add_item(AuthorButton(author, row=row))
        else:
            self.add_item(AuthorSelectMenu(authors))

    def show_results_buttons(self):
        """Switch to results action buttons (Play Again)."""
        self.clear_items()
        self.add_item(PlayAgainButton())

    async def on_timeout(self):
        """Disable all interactive components on timeout."""
        for item in self.children:
            if isinstance(item, (discord.ui.Button, discord.ui.Select)):
                item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


class QuoteGame(commands.Cog, name="QuoteGame"):
    """Quote matching minigame cog using Dungewar Random Quote API."""

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

    async def fetch_unique_quotes(self, count: int = 2) -> List[Tuple[str, str]]:
        """Fetch quotes from api.dungewar.com/random-quote and ensure distinct authors."""
        session = await self.get_session()
        fetch_n = max(count + 4, 4)
        url = f"{API_URL}?n={fetch_n}"

        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    parsed_list: List[Tuple[str, str]] = []
                    seen_authors = set()

                    for raw_quote in data:
                        parsed = parse_quote_string(raw_quote)
                        if parsed:
                            text, author = parsed
                            if author not in seen_authors:
                                seen_authors.add(author)
                                parsed_list.append((text, author))
                                if len(parsed_list) == count:
                                    break
                    return parsed_list
        except Exception as e:
            print(f"[QuoteGame Cog] Error fetching quotes: {e}")

        return []

    @commands.hybrid_command(
        name="quotegame",
        description="Play a quote matching minigame! Guess who said each quote.",
        aliases=["qgame", "matchquote", "quotematch"],
        help="Play a quote matching minigame. Usage: `/quotegame [count]` or `.quotegame [count]`"
    )
    @discord.app_commands.describe(
        count="Number of quotes and people to match (default: 2, min: 2, max: 10)"
    )
    async def quotegame(self, ctx: commands.Context, count: commands.Range[int, 2, 10] = 2):
        """Start a new quote matching minigame."""
        count = max(2, min(int(count), 10))

        quotes = await self.fetch_unique_quotes(count=count)
        if not quotes or len(quotes) < 2:
            embed = discord.Embed(
                title="⚠️ Error Loading Quotes",
                description="Unable to fetch random quotes from `api.dungewar.com/random-quote`. Please try again later.",
                color=0xEF4444
            )
            await ctx.send(embed=embed)
            return

        session = QuoteGameSession(
            quotes=quotes,
            initiator_name=ctx.author.display_name
        )

        view = QuoteGameView(self, session)
        embed = build_game_embed(session)
        message = await ctx.send(embed=embed, view=view)
        view.message = message


async def setup(bot: commands.Bot):
    await bot.add_cog(QuoteGame(bot))
