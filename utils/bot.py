import logging

from discord.ext import commands

import config

logger = logging.getLogger(__file__)

bot = commands.Bot(command_prefix=config.config.get('COMMAND_PREFIX', '!'))

# @bot.command(name='<command name>')
# @admin_command

_admin_required = commands.has_role(config.config.get('ADMIN_ROLE', 'Blue Shirt'))
_admin_owner_required = commands.check_any(_admin_required, commands.is_owner())

if 'testing' in config.mode:
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
        raise exception


@bot.event
async def on_ready() -> None:
    logger.info(f"{bot.user} has connected to Discord!")
    if 'testing' in config.mode:
        logger.info("Bot is running in test mode")
    if 'debug' in config.mode:
        logger.info("Bot is running in debug mode")


def setup_logging() -> None:
    formatter = logging.Formatter('%(asctime)s - %(levelname)% - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(console_handler)

    if config.config.get('LOG_FILE'):
        file_handler = logging.FileHandler(config.config['LOG_FILE'])
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    if 'debug' in config.mode:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
