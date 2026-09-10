import discord
import os
from discord.ext import commands
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from utils import reply

timezone = ZoneInfo("America/Los_Angeles")

class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def current_log_path():
        date = datetime.now(timezone).strftime("%m-%d-%Y")
        return f"logs/{date}.txt"

    @staticmethod
    def log_path_days_ago(days_ago: int):
        date = (datetime.now(timezone) - timedelta(days=days_ago)).strftime("%m-%d-%Y")
        return f"logs/{date}.txt"

    # .log
    @commands.hybrid_command(help="Logs an event with a timestamp. Usage: `.log <message>`")
    @commands.has_role('grape')
    async def log(self, ctx, *, message):
        timestamp = ctx.message.created_at.astimezone(timezone).strftime('%I:%M:%S %p')
        with open(self.current_log_path(), "a") as f:
            if any(role.name == "invisible logs" for role in ctx.author.roles):
                f.write('*')
            f.write(f'{timestamp} ({ctx.author.name}): {message}\n')
        if ctx.interaction is None:
            await ctx.message.add_reaction('🧀')
        else:
            await ctx.send('🧀')

    async def send_log(self, ctx: commands.Context, message, include_hidden):
        if message is None:
            path = self.current_log_path()
        else:
            query = message.strip()
            if query.isdigit():
                path = self.log_path_days_ago(int(query))
            else:
                path = f"logs/{query}.txt"
        path = os.path.realpath(path)
        
        # prevent directory traversal attack
        logs_dir = os.path.realpath('logs')
        if os.path.commonpath([path, logs_dir]) != os.path.commonpath([logs_dir]):
            await reply(ctx.message, "heck you (access denied)")
            return
        try:
            with open(path, "r") as log_file:
                lines = log_file.readlines()
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

                await reply(ctx.message, f"-# {path[-14:-4]}\n```{''.join(chunks[0])}```")
                for chunk in chunks[1:min(6, len(chunks))]: # limit to 6 chunks
                    await ctx.send(f"```{''.join(chunk)}```")
        except FileNotFoundError:
            await reply(ctx.message, f"file '{path}' not found. usage: `.view mm-dd-yyyy` or `.view N` (days ago)")
        except Exception as e:
            await reply(ctx.message, f"error: {e}")

    # .view
    @commands.command(help="Views a log file. usage: `.view mm-dd-yyyy` or `.view N` (days ago)")
    async def view(self, ctx, *, message=None):
        await self.send_log(ctx, message, include_hidden=False)

    # .view2
    @commands.command()
    @commands.has_role('view2er')
    async def view2(self, ctx, *, message=None):
        await self.send_log(ctx, message, include_hidden=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Logging(bot))
