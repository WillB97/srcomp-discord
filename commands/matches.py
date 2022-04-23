import logging
from typing import List, Optional, NamedTuple
from datetime import datetime, timezone
from collections import defaultdict

import requests
from discord.ext import commands

from utils.bot import bot, admin_command
import utils.config as config
from utils.channels import get_channel, get_team_channel, log_error_and_reply

logger = logging.getLogger(__file__)


class TeamMatch(NamedTuple):
    """ A team's match
    """
    start_time: datetime
    num: int
    corner: int
    arena: str
    name: str


def load() -> None:
    """ A no-op to stop linters complaining
    """
    pass


def format_team_matches(tla: str, matches: List[TeamMatch], all: bool = False) -> Optional[str]:
    """ Format the matches to be announced to a team as a string in a code block
    """
    if not(matches):
        return None

    text = f"Hello {tla}, your matches "
    text += "are:\n" if all else "for today are:\n"
    text += "```\n"

    for match in matches:
        if all:
            text += f"{match.start_time.astimezone():%d/%m %H:%M}\t"
        else:
            text += f"{match.start_time.astimezone():%H:%M}\t"
        text += f"{match.name}\t corner: {match.corner}\n"

    text += "```"
    return text


@bot.command(name='announce')
@admin_command
async def announce_cmd(ctx: commands.Context, all: Optional[str] = None) -> None:
    """ Announce upcoming matches to teams, defaults to only the current day
        - all: set to all to announce all upcomming matches, not just today's
    """
    missing_teams = []
    successful_teams = []

    send_all = (all == 'all')
    http_api = config.config.get('HTTP_API')
    if http_api is None:
        await log_error_and_reply(ctx, 'HTTP_API is not defined in environment')
        return

    if not http_api.endswith('/'):
        http_api += '/'

    with ctx.typing():  # provides feedback that the bot is processing
        r = requests.get(http_api + 'matches')
        if r.status_code != 200:
            await log_error_and_reply(ctx, 'HTTP_API is not accessible')
            return

        matches = r.json().get('matches')
        if matches is None:
            await log_error_and_reply(ctx, "Couldn't find matches")
            return

        # reindex by team
        team_matches = defaultdict(list)
        for match in matches:
            for corner, team in enumerate(match['teams']):
                if team is None or team == '???':
                    continue

                team_matches[team].append(TeamMatch(
                    datetime.fromisoformat(match['times']['game']['start']),
                    match['num'],
                    corner,
                    match['arena'],
                    match['display_name']
                ))

        current_time = datetime.now(timezone.utc)
        for team, match_data in team_matches.items():
            # filter out past matches
            future_matches = [x for x in match_data if x.start_time > current_time]

            if not send_all:
                # filter matches to current day
                future_matches = [
                    x for x in future_matches
                    if x.start_time.date() == current_time.date()
                ]

            # send to team channel
            team_channel = await get_team_channel(ctx, team)
            if team_channel is None:
                # accumulate missing team channels
                missing_teams.append(team)
                continue

            team_text = format_team_matches(team, future_matches, send_all)
            if team_text is not None:
                await team_channel.send(team_text)
                successful_teams.append(team)

    await ctx.reply(
        f"Successfully announced to {len(successful_teams)} teams.\n"
        + (f"Failed to find: {missing_teams}" if missing_teams else "")
    )


@bot.command(name='state')
@admin_command
async def state_cmd(ctx: commands.Context) -> None:
    """ Print the current state of the APIs
    """
    # API link defined and fetchable
    http_api = config.config.get('HTTP_API')
    if http_api is None:
        await log_error_and_reply(ctx, 'HTTP_API is not defined in environment')
        return

    http_stream = config.config.get('HTTP_STREAM')
    if http_stream is None:
        await log_error_and_reply(ctx, 'HTTP_STREAM is not defined in environment')
        return

    with ctx.typing():  # provides feedback that the bot is processing
        if not http_api.endswith('/'):
            http_api += '/'

        r = requests.get(http_api + 'current')
        api_accessible = (r.status_code == 200)
        if api_accessible:
            delay = r.json().get('delay', 'NA')
        else:
            delay = 'NA'

    publish_enable = 'enabled' if config.config.get('PUBLISH_STREAM') else 'disabled'
    shepherding_channel = config.config.get('SHEPHERDING_CHANNEL')
    matches_channel = config.config.get('MATCHES_CHANNEL')

    if shepherding_channel is not None:
        shepherding_obj = await get_channel(ctx, shepherding_channel)
        if shepherding_obj:
            shepherding_channel = f"<#{shepherding_obj.id}>"
    if matches_channel is not None:
        matches_obj = await get_channel(ctx, matches_channel)
        if matches_obj:
            matches_channel = f"<#{matches_obj.id}>"

    await ctx.send(
        "```"
        f"HTTP API: {http_api}\n"
        f"API accessible: {api_accessible}\n"
        f"Current delay: {delay} seconds\n"
        f"Stream URL: {http_stream}\n"
        f"Stream active: {config.config.get('stream_connected', 'False')}\n"
        f"Publishing: {publish_enable}\n"
        "```"
        f"Shepherding channel: {shepherding_channel}\n"
        f"Matches channel: {matches_channel}\n"
    )
