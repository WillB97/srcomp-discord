import logging
from typing import cast, Optional

import discord
from discord import TextChannel
from discord.ext import commands

import utils.config as config

logger = logging.getLogger(__file__)


async def get_channel(
    ctx: commands.Context,
    channel_name: str,
) -> Optional[TextChannel]:
    channel_name = channel_name.lower()  # all text/voice channels are lowercase
    guild = ctx.guild
    if 'testing' in config.mode:
        # Always return calling channel
        return cast(TextChannel, ctx.channel)

    # get team's channel by name
    if guild is None:
        raise commands.NoPrivateMessage
    channel = discord.utils.get(
        guild.channels,
        name=channel_name,
    )

    if not channel:
        await log_error_and_reply(
            ctx,
            f"# Channel {channel_name} not found, unable to send message",
        )
        return None
    elif not isinstance(channel, TextChannel):
        await log_error_and_reply(
            ctx,
            f"# {channel.name} is not a text channel, unable to send message",
        )
        return None

    return channel


async def get_team_channel(
    ctx: commands.Context,
    tla: str,
) -> Optional[TextChannel]:
    channel = await get_channel(ctx, f"{config.config.get('TEAM_PREFIX', 'team-')}{tla.lower()}")

    return channel


async def log_error_and_reply(ctx: commands.Context, error_str: str) -> None:
    logger.error(error_str)
    await ctx.reply(error_str)
