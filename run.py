import discord
from dotenv import load_dotenv
from discord.ext.commands import AutoShardedBot
from os import getenv
from models import PostgreSQL, AbstractDataBase

load_dotenv()  # reloads .env to memory


class WeverseBot(AutoShardedBot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options.get("options"))

        self.conn: AbstractDataBase = PostgreSQL(**options.get("db_kwargs"))  # db connection


if __name__ == '__main__':
    intents = discord.Intents.default()
    # intents.members = True  # turn on privileged members intent
    # intents.presences = True  # turn on presences intent

    kwargs = {
        "options": {
            "case_insensitive": True,
            "owner_id": int(getenv("BOT_OWNER_ID")),
            "intents": intents
        },
        "db_kwargs": {
            "host": getenv("POSTGRES_HOST"),
            "database": getenv("POSTGRES_DATABASE"),
            "user": getenv("POSTGRES_USER"),
            "password": getenv("POSTGRES_PASSWORD"),
            "port": getenv("POSTGRES_PORT")
        }
    }

    bot = WeverseBot(getenv("BOT_PREFIX"), **kwargs)

    cogs = ["BotInfo", "Weverse"]

    for cog in cogs:
        bot.load_extension(f"cogs.{cog}")

    bot.run(getenv("BOT_TOKEN"))
