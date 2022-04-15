from os import environ, path
from dotenv import dotenv_values

# importing this module fully means this will only be run once
config = {
    **dotenv_values(path.join(path.dirname(__file__), "..", ".env")),
    **environ,  # override loaded values with environment variables
}

# modes:
# debug - enable debug level logging
# testing - post all messages to calling channel only, allow DMs
mode = [x.lower() for x in config.get('DISCORD_MODE', '').split()]
