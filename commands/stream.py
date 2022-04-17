import json
import asyncio
import logging
from typing import Optional
from datetime import datetime, timezone

from discord import TextChannel
from discord.ext import commands
from aiohttp_sse_client import client as sse_client

import utils.config as config
from utils.bot import bot, admin_command, get_channel, get_team_channel
from commands.matches import TeamMatch

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

    while True:
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

                        await process_event_stream(event.data)
        except asyncio.CancelledError:
            raise
        except BaseException as e:
            logger.exception(e)
        finally:
            # track that the stream failed
            config.config['stream_connected'] = 'False'
            logger.error("Stream disconnected")

        await asyncio.sleep(2)


async def process_event_stream(match_data: str) -> None:
    announcable_matches = []
    for match in json.loads(match_data):
        logger.info(f"New shepherding: {match['teams']}")
        for corner, team in enumerate(match['teams']):
            if team is None or team == '???':
                continue

            match_name = match['display_name']

            announcable_matches.append((team, TeamMatch(
                datetime.fromisoformat(match['times']['game']['start']),
                match['num'],
                corner,
                match['arena'],
                match_name
            )))

        # message shepherding channel
        if shepherding := config.config.get('SHEPHERDING_CHANNEL'):
            channels = await get_channel(bot, shepherding)
            team_str = ', '.join(x for x in match['teams'] if x)
            for channel in channels:
                await channel.send(
                    f"Next match: {match_name} between {team_str}"
                )

        # message match channel
        if match_chan := config.config.get('MATCHES_CHANNEL'):
            channels = await get_channel(bot, match_chan)
            delay = (
                datetime.fromisoformat(match['times']['game']['start'])
                - datetime.now(timezone.utc)
            ).total_seconds()
            msg = f"{match_name} is starting now"
            for channel in channels:
                asyncio.get_running_loop().call_later(
                    delay,
                    asyncio.create_task,
                    channel.send(msg),
                )

    for tla, match in announcable_matches:
        # send messages to team channels
        team_channels = await get_team_channel(bot, tla)
        for team_channel in team_channels:
            await team_channel.send(
                f"Your next match is starting at {match.start_time.astimezone():%H:%M}, "
                "you should head down now"
            )
