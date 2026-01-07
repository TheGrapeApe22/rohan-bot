import discord
from discord.ext import commands, tasks
from dataclasses import dataclass
from typing import Dict, Optional
from utils import reply

# High-level: This cog manages independent reminder streams per user, each with its own loop, delay, and last reminder message.

@dataclass
class ReminderStream:
    reminder_loop: tasks.Loop
    target_context: commands.Context
    last_reminder_message: Optional[discord.Message]
    current_delay_minutes: float


class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.default_delay_minutes: float = 5.0
        self.user_streams: Dict[int, ReminderStream] = {}

    async def _run_user_reminder(self, target_context):
        user_id = target_context.author.id
        stream = self.user_streams.get(user_id)
        if stream is None:
            return
        # delete last message
        if stream.last_reminder_message:
            try:
                await stream.last_reminder_message.delete()
            except Exception:
                pass
        # send reminder message
        try:
            loop_index = stream.reminder_loop.current_loop
            stream.last_reminder_message = await target_context.send(f"-# what are you doing {target_context.author.mention} ({loop_index})")
        except Exception as e:
            await target_context.send(f"error: unable to send reminder ({e})")
            stream.reminder_loop.cancel()

    def create_loop(self, minutes, user_id: int) -> tasks.Loop:
        return tasks.Loop(
            self._run_user_reminder,
            seconds=0.0,
            minutes=minutes,
            hours=0.0,
            time=discord.utils.MISSING,
            count=None,
            reconnect=True,
            name=f"user-{user_id}-reminder",
        )

    @commands.command(name="start")
    @commands.has_role('grape')
    async def start(self, ctx):
        user_id = ctx.author.id
        if user_id in self.user_streams and self.user_streams[user_id].reminder_loop.is_running():
            await reply(ctx.message, "already running")
            return
        initial_delay = self.user_streams[user_id].current_delay_minutes if user_id in self.user_streams else self.default_delay_minutes
        user_stream = ReminderStream(
            reminder_loop=self.create_loop(initial_delay, user_id),
            target_context=ctx,
            last_reminder_message=None,
            current_delay_minutes=initial_delay,
        )
        self.user_streams[user_id] = user_stream
        user_stream.reminder_loop.start(ctx)
        await reply(ctx.message, "started")

    @commands.command(name="stop")
    @commands.has_role('grape')
    async def stop(self, ctx):
        user_id = ctx.author.id
        stream = self.user_streams.get(user_id)
        if not stream or not stream.reminder_loop.is_running():
            await reply(ctx.message, "not running")
            return
        stream.reminder_loop.cancel()
        stream.last_reminder_message = None
        await reply(ctx.message, "stopped")

    @commands.command(name="setdelay")
    @commands.has_role('grape')
    async def setdelay(self, ctx, minutes):
        user_id = ctx.author.id
        safe_delay = max(0.1, minutes)
        stream = self.user_streams.get(user_id)
        if not stream:
            stream = ReminderStream(
                reminder_loop=self.create_loop(safe_delay, user_id),
                target_context=ctx,
                last_reminder_message=None,
                current_delay_minutes=safe_delay,
            )
            self.user_streams[user_id] = stream
        else:
            stream.target_context = ctx
            stream.current_delay_minutes = safe_delay
            stream.reminder_loop.change_interval(minutes=safe_delay)
        await reply(ctx.message, f"delay changed to {safe_delay} minutes")
        if stream.reminder_loop.is_running():
            stream.reminder_loop.restart(ctx)

    @commands.command(name="delay")
    @commands.has_role('grape')
    async def delay(self, ctx):
        user_id = ctx.author.id
        stream = self.user_streams.get(user_id)
        current_delay = stream.current_delay_minutes if stream else self.default_delay_minutes
        await reply(ctx.message, f"current delay is {current_delay} minutes")


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
