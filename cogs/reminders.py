import discord
from discord.ext import commands, tasks
from dataclasses import dataclass
from typing import Dict, Optional
from utils import reply

# cog managing reminder streams per user, each with its own loop, delay, etc.

@dataclass
class ReminderStream:
    reminder_loop: tasks.Loop
    target_context: commands.Context
    last_reminder_message: Optional[discord.Message]
    delay_minutes: float
    message_content: str
    def __init__(self, target_context: commands.Context, run_user_reminder, delay_minutes: float=5, message_content: str=None):
        self.target_context = target_context
        self.last_reminder_message = None
        self.delay_minutes = delay_minutes
        self.message_content = message_content if message_content is not None else f"reminder"
        self.reminder_loop = tasks.Loop(
            run_user_reminder,
            seconds=0.0,
            minutes=self.delay_minutes,
            hours=0.0,
            time=discord.utils.MISSING,
            count=None,
            reconnect=True,
            name=f"user-{target_context.author.id}-reminder",
        )

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.default_delay_minutes: float = 5.0
        self.user_streams: Dict[int, ReminderStream] = {}

    async def _run_user_reminder(self, target_context: commands.Context):
        stream = self.user_streams.get(target_context.author.id)
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
            stream.last_reminder_message = await target_context.send(f"{stream.message_content}\n-# <@{target_context.author.id}> ({stream.reminder_loop.current_loop})")
        except Exception as e:
            await target_context.send(f"error: unable to send reminder ({e})")
            stream.reminder_loop.cancel()
    
    # return user_streams[id], create one if it doesn't exist
    def get_stream(self, target_context: commands.Context) -> ReminderStream:
        id = target_context.author.id
        if not self.user_streams.get(id):
            self.user_streams[id] = ReminderStream(target_context=target_context, run_user_reminder=self._run_user_reminder)
        return self.user_streams[id]

    @commands.command(name="start", help="Starts the reminder stream. Usage: `.start`")
    async def start(self, ctx):
        stream = self.get_stream(ctx)
        if stream.reminder_loop.is_running():
            await reply(ctx.message, "already running")
            return
        stream.reminder_loop.start(ctx)
        await reply(ctx.message, "started")

    @commands.command(name="stop", help="Stops the reminder stream. Usage: `.stop`")
    async def stop(self, ctx):
        stream = self.get_stream(ctx)
        if not stream.reminder_loop.is_running():
            await reply(ctx.message, "not running")
            return
        stream.reminder_loop.cancel()
        await reply(ctx.message, "stopped")

    @commands.command(name="setdelay", help="Sets the reminder delay in minutes. Usage: `.setdelay <minutes>`")
    async def setdelay(self, ctx, minutes: float):
        new_delay = max(0.1, minutes)
        stream = self.get_stream(ctx)
        # set delay
        stream.delay_minutes = new_delay
        stream.reminder_loop.change_interval(minutes=new_delay)
        await reply(ctx.message, f"delay changed to {new_delay} minutes")
        if stream.reminder_loop.is_running():
            stream.reminder_loop.restart(ctx)

    @setdelay.error
    async def setdelay_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await reply(ctx.message, "invalid minutes, please provide a single number (e.g., 5 or 0.5)")
        else:
            raise error

    @commands.command(name="delay", help="Shows the current reminder delay in minutes. Usage: `.delay`")
    async def delay(self, ctx):
        await reply(ctx.message, f"current delay is {self.get_stream(ctx).delay_minutes} minutes")
    
    @commands.command(name="setmessage", help="Sets the reminder message content. Sends a template if no message provided. Usage: `.setmessage <message>`")
    async def setmessage(self, ctx, *, message: str=None):
        if message is None or message.strip() == "":
            await reply(ctx.message, f"```.setmessage {self.get_stream(ctx).message_content}```")
            return
        self.get_stream(ctx).message_content = message
        await reply(ctx.message, f"reminder message set!")
    
    @commands.command(name="append", help="Appends text to the current reminder message content. Usage: `.append <text>`")
    async def append(self, ctx, *, text: str):
        stream = self.get_stream(ctx)
        stream.message_content += f"\n* {text}"
        await reply(ctx.message, "text appended to reminder message")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
