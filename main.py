#!/usr/bin/env python3
import logging

import utils.config as config
import commands.matches
import commands.stream
from utils.bot import bot, setup_logging

logger = logging.getLogger(__file__)


def main() -> None:
    setup_logging()

    commands.matches.load()
    commands.stream.load()

    discord_token = config.config.get('DISCORD_TOKEN')
    if discord_token is None:
        logger.critical('DISCORD_TOKEN must be specified in .env')
        exit(1)

    bot.run(discord_token)


if __name__ == "__main__":
    main()
