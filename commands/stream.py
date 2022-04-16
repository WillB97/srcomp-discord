import logging
from typing import Optional

from discord import TextChannel
from discord.ext import commands

import utils.config as config
from utils.bot import bot, admin_command

logger = logging.getLogger(__file__)


def load() -> None:
    """ A no-op to stop linters complaining
    """
    pass


# publish [enable|disable]
@bot.command(name='publish')
@admin_command
async def publish_cmd(
    ctx: commands.Context,
    enable: bool = False,
) -> None:
    """
    """
    config.config['PUBLISH_STREAM'] = str(enable)
    await ctx.reply(f"Match publishing {'enabled' if enable else 'disabled'}")


# set-shepherding
@bot.command(name='set-shepherding')
@admin_command
async def set_shepherding_cmd(
    ctx: commands.Context,
    channel: Optional[TextChannel] = None,
) -> None:
    """
    """
    # TODO save this to env file
    if channel is None:
        config.config['SHEPHERDING_CHANNEL'] = None
        await ctx.reply("Shepherding channel disabled")
    else:
        config.config['SHEPHERDING_CHANNEL'] = channel.name
        await ctx.reply(f"Shepherding channel set to {channel.name}")


# set-matches
@bot.command(name='set-matches')
@admin_command
async def set_matches_cmd(
    ctx: commands.Context,
    channel: Optional[TextChannel] = None,
) -> None:
    """
    """
    # TODO save this to env file
    if channel is None:
        config.config['MATCHES_CHANNEL'] = None
        await ctx.reply("Matches channel disabled")
    else:
        config.config['MATCHES_CHANNEL'] = channel.name
        await ctx.reply(f"Matches channel set to {channel.name}")
