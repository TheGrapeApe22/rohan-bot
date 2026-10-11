import os
import discord
from discord.ext import commands
from utils.send import get_command_string, send_log

MY_ID = os.getenv("MY_ID")

class CommandAudit(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _listed_channel_ids() -> set[int]:
        with open('data/ignore_channels.txt', "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [int(line.strip()) for line in lines if line.strip() and not line.startswith("#")]

    async def _should_send_log(self, channel, author, guild) -> bool:
        # check hardcoded list
        if channel.id in self._listed_channel_ids():
            return False

        # check if i am the person who ran the command
        if author.id == MY_ID:
            return False

        # if this is in a server
        if guild is not None:
            # if i am not in server, send log
            if guild.get_member(MY_ID) is None:
                return True
            # if i can view the channel, don't send log
            if channel.permissions_for(guild.get_member(MY_ID)).view_channel:
                return False
            return True

        # if this is in a DM, send log if I am not a recipient
        if isinstance(channel, discord.DMChannel):
            return not any(user.id == MY_ID for user in channel.recipients)

        return True

    async def _send_audit_log(self, author_id, channel, guild, content) -> None:
        location = f'channel (<#{channel.id}>)'

        if guild is None:
            location += f", DM of type [{channel.type}]"
            if isinstance(channel, discord.DMChannel) or isinstance(channel, discord.GroupChannel):
                location += f" with recipients [{', '.join(f'<@{user.id}>' for user in channel.recipients)}]"
            if isinstance(channel, discord.GroupChannel):
                location += f" named [{channel.name}]"
        else:
            location += f' named [{channel.name}] in server named [{guild.name}] with id [{guild.id}]'
        
        await send_log(f"<@{author_id}> used `{content}` in {location}.", self.bot)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        if ctx.interaction is not None:
            return # avoid double counting interactions

        if await self._should_send_log(ctx.channel, ctx.author, ctx.guild):
            await self._send_audit_log(
                ctx.author.id,
                ctx.channel,
                ctx.guild,
                ctx.message.content,
            )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type is not discord.InteractionType.application_command:
            return

        if await self._should_send_log(interaction.channel, interaction.user, interaction.guild):
            await self._send_audit_log(
                interaction.user.id,
                interaction.channel,
                interaction.guild,
                get_command_string(interaction),
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommandAudit(bot))
