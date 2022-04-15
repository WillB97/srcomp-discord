#!/usr/bin/env python3
import logging

from discord.ext import commands

import utils.config as config
from utils.bot import bot, admin_command, setup_logging
from utils.channels import log_error_and_reply

logger = logging.getLogger(__file__)


@bot.command(name='ping')
@admin_command
async def test_cmd(ctx: commands.Context) -> None:
    await log_error_and_reply(ctx, 'pong')


def main() -> None:
    setup_logging()

    discord_token = config.config.get('DISCORD_TOKEN')
    if discord_token is None:
        logger.critical('DISCORD_TOKEN must be specified in .env')
        exit(1)

    bot.run(discord_token)


if __name__ == "__main__":
    main()
