import json
import logging
from typing import Optional

from discord import TextChannel
from discord.ext import commands
from aiohttp_sse_client import client as sse_client

import utils.config as config
from utils.bot import bot, admin_command

logger = logging.getLogger(__file__)

event_stream_task = None


def load() -> None:
    """
    """
    global event_stream_task
    event_stream_task = bot.loop.create_task(watch_event_stream())


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
    logger.info(f"Match publishing {'enabled' if enable else 'disabled'}")
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
        logger.info("Shepherding channel disabled")
        await ctx.reply("Shepherding channel disabled")
    else:
        config.config['SHEPHERDING_CHANNEL'] = channel.name
        logger.info(f"Shepherding channel set to {channel.name}")
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


async def watch_event_stream() -> None:
    if config.config.get('HTTP_STREAM') is None:
        logger.error('HTTP_STREAM is not defined in environment')
        return

    # TODO retry logic
    try:
        async with sse_client.EventSource(
            config.config['HTTP_STREAM'],
            timeout=0,
        ) as event_source:
            logger.info(f"Event stream connected to {config.config['HTTP_STREAM']}")
            config.config['stream_connected'] = 'True'
            async for event in event_source:
                if event.message == 'current-shepherding-matches':
                    if config.config.get('PUBLISH_STREAM', 'False') != 'True':
                        # supress handling events when publishing is disabled
                        continue

                    for match in json.loads(event.data):
                        print(match['display_name'], match['teams'])

    finally:
        # track that the stream failed
        config.config['stream_connected'] = 'False'
        logger.error("Stream disconnected")
