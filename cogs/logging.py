from discord.ext import commands
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils.perms import enforce_whitelist
from utils.reply import reply
from utils.send import send
from utils import file_paths as paths

timezone = ZoneInfo("America/Los_Angeles")

class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def current_log_path():
        date = datetime.now(timezone).strftime("%m-%d-%Y")
        return paths.LOGS / f"{date}.txt"

    @staticmethod
    def log_path_days_ago(days_ago: int):
        date = (datetime.now(timezone) - timedelta(days=days_ago)).strftime("%m-%d-%Y")
        return paths.LOGS / f"{date}.txt"

    # .log
    @commands.hybrid_command(help="Logs an event with a timestamp. Usage: `.log <message>`")
    # @commands.has_role('grape')
    async def log(self, ctx, *, message):
        timestamp = ctx.message.created_at.astimezone(timezone).strftime('%I:%M:%S %p')
        paths.LOGS.mkdir(parents=True, exist_ok=True)
        with self.current_log_path().open("a") as f:
            f.write(f'{timestamp} ({ctx.author.name}): {message}\n')
        if ctx.interaction is None:
            await ctx.message.add_reaction('🧀')
        else:
            await send(ctx, '🧀')

    async def send_logs(self, ctx: commands.Context, message, include_hidden):
        if message is None:
            path = self.current_log_path()
        else:
            query = message.strip()
            if query.isdigit():
                path = self.log_path_days_ago(int(query))
            else:
                path = paths.LOGS / f"{query}.txt"
        path = path.resolve()
        
        # prevent directory traversal attack
        if not path.is_relative_to(paths.LOGS.resolve()):
            await send(ctx, "heck you (access denied)")
            return
        try:
            lines = path.read_text().splitlines(keepends=True)
            if not include_hidden:
                lines = [line for line in lines if not line.startswith('*')]

            chunks = []
            current_chunk = []
            current_len = 0
            max_chunk_len = 1500

            for line in lines:
                line_len = len(line)
                if current_chunk and (current_len + line_len > max_chunk_len):
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_len = 0
                current_chunk.append(line)
                current_len += line_len

            if current_chunk:
                chunks.append(current_chunk)

            if not chunks:
                chunks = [["(no visible log lines)\n"]]

            await send(ctx, f"-# {path.stem}\n```{''.join(chunks[0])}```")
            for chunk in chunks[1:min(6, len(chunks))]: # limit to 6 chunks
                await send(ctx, f"```{''.join(chunk)}```")
        except FileNotFoundError:
            await send(ctx, f"no logs on this date. usage: `view mm-dd-yyyy` or `view N` (days ago)")

    # .view
    @commands.hybrid_command(help="Views a log file. usage: `view mm-dd-yyyy` or `view N` (days ago)")
    async def view(self, ctx, *, log_file=None):
        await enforce_whitelist(ctx)
        await self.send_logs(ctx, log_file, include_hidden=False)

    # .view2
    # @commands.command()
    # @commands.has_role('view2er')
    # async def view2(self, ctx, *, message=None):
    #     await self.send_logs(ctx, message, include_hidden=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))
