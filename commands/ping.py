import logging

from discord.ext import commands

from utils.bot import bot, admin_command
from utils.channels import log_error_and_reply

logger = logging.getLogger(__file__)


def load() -> None:
    """ A no-op to stop linters complaining
    """
    pass


@bot.command(name='ping')
@admin_command
async def test_cmd(ctx: commands.Context) -> None:
    await log_error_and_reply(ctx, 'pong')
