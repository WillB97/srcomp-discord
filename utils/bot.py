import logging
from typing import List

import discord
from discord import TextChannel
from discord.ext import commands

import utils.config as config

logger = logging.getLogger(__file__)

bot = commands.Bot(command_prefix=config.config.get('COMMAND_PREFIX', '!'))

# @bot.command(name='<command name>')
# @admin_command

_admin_required = commands.has_role(config.config.get('ADMIN_ROLE', 'Blue Shirt'))
_admin_owner_required = commands.check_any(_admin_required, commands.is_owner())

if 'testing' in config.mode:
    # Allow DMs
    admin_command = _admin_owner_required
else:
    admin_command = commands.check_any(commands.guild_only(), _admin_owner_required)


@bot.event
async def on_command_error(ctx: commands.Context, exception: commands.CommandError) -> None:
    if isinstance(exception, commands.MissingRequiredArgument):
        logger.info(f"{ctx.author} ran '{ctx.message.content}' on {ctx.guild}:{ctx.channel}")
        logger.error(f"A required argument '{exception.param}' is missing")
        await ctx.send(f"A required argument '{exception.param}' is missing")
        await ctx.send_help(ctx.command)  # print corresponding command help
    else:
        logger.exception(exception)
        await ctx.send(f"An exception occurred: {exception}")


@bot.event
async def on_ready() -> None:
    logger.info(f"{bot.user} has connected to Discord!")
    if 'testing' in config.mode:
        logger.info("Bot is running in test mode")
    if 'debug' in config.mode:
        logger.info("Bot is running in debug mode")


def setup_logging() -> None:
    """ Print logging from all loggers to terminal and file if LOG_FILE is set.
        Logging level is increased from INFO to DEBUG if DISCORD_MODE is set to debug.
    """
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create a handler to output to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)

    if (log := config.config.get('LOG_FILE')) is not None:
        # Create a handler to also output to file
        file_handler = logging.FileHandler(log)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if 'debug' in config.mode:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)


async def get_channel(
    bot: commands.Bot,
    channel_name: str,
) -> List[TextChannel]:
    """ Get a channel object when not with a command callback
    """
    if 'testing' in config.mode:
        # always DM owner
        app_info = await bot.application_info()
        owner_dm = app_info.owner.dm_channel
        if owner_dm:
            return [owner_dm]
        return []

    channels = []

    for guild in bot.guilds:
        channel = discord.utils.get(
            guild.channels,
            name=channel_name,
        )
        if isinstance(channel, TextChannel):
            channels.append(channel)

    if not channels:
        logger.warning(f"Channel {channel_name} not found in any guild")

    return channels


async def get_team_channel(
    bot: commands.Bot,
    tla: str,
) -> List[TextChannel]:
    """ Get the channel for tla when not with a command callback
    """
    channel = await get_channel(bot, f"{config.config.get('TEAM_PREFIX', 'team-')}{tla.lower()}")

    return channel
