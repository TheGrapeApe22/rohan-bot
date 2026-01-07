import discord
from discord.ext import commands, tasks
from utils import reply

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current_delay = 5.0
        self.target_context: commands.Context | None = None
        self.last_reminder: discord.Message | None = None

    @tasks.loop(minutes=5.0)
    async def reminders(self):
        if not self.target_context:
            return
        try:
            # delete last reminder
            if self.last_reminder:
                await self.last_reminder.delete()
            # what are you doing
            self.last_reminder = await reply(self.target_context.message, f"-# what are you doing {self.target_context.author.mention} ({self.reminders.current_loop})")
        except Exception:
            await reply(self.target_context.message, f"error: unable to send reminder ({Exception})")
            self.reminders.cancel()

    @commands.command(name="start")
    @commands.has_role('grape')
    async def start(self, ctx: commands.Context):
        if not self.reminders.is_running():
            self.target_context = ctx
            self.reminders.start()
            await reply(ctx.message, "started")
        else:
            await reply(ctx.message, "already running")

    @commands.command(name="stop")
    @commands.has_role('grape')
    async def stop(self, ctx: commands.Context):
        if self.reminders.is_running():
            self.reminders.cancel()
            self.target_context = None
            self.last_reminder = None
            await reply(ctx.message, "stopped")
        else:
            await reply(ctx.message, "not running")

    @commands.command(name="setdelay")
    @commands.has_role('grape')
    async def setdelay(self, ctx: commands.Context, minutes: float):
        self.current_delay = max(0.1, minutes)
        self.reminders.change_interval(minutes=self.current_delay)
        # restart so the new delay takes effect immediately
        await reply(ctx.message, f"delay changed to {self.current_delay} minutes")
        if self.reminders.is_running():
            self.reminders.restart()

    @commands.command(name="delay")
    @commands.has_role('grape')
    async def delay(self, ctx: commands.Context):
        await reply(ctx.message, f"current delay is {self.current_delay} minutes")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
