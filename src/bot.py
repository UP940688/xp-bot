from datetime import datetime
from sys import stderr

import discord
from discord.ext import commands

import config
from database import DB

intents = discord.Intents.default()
intents.members = True


def get_prefixes(bot, message=None):
    prefixes = bot.db.get_prefixes()
    return [f"<@!{bot.user.id}> ", f"<@{bot.user.id}> "] + prefixes


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefixes,
            case_insensitive=True,
            description="Manages XP & Levels!",
            dm_mode=True,
            intents=intents,
        )
        self.db = DB("bot.db")

        self.remove_command("help")
        for cog in config.cogs:
            try:
                self.load_extension(cog)
            except Exception as e:
                print(f"Error: Failed to load cog: {e}", file=stderr)

    def run(self):
        super().run(config.token, reconnect=True)

    async def on_ready(self):
        self.level_cog = self.get_cog("Level")
        self.guild = discord.utils.get(self.guilds, id=config.guild_id)
        self.main_channel = discord.utils.get(self.guild.channels, id=config.main_channel_id)
        self.level_up_channel = discord.utils.get(self.guild.channels, id=config.level_channel_id)
        print("Bot ready at", datetime.now())

    async def on_message(self, message):
        if message.author.bot:
            return
        try:
            await self.process_commands(message)
            if not isinstance(message.channel, discord.DMChannel):
                await self.level_cog.process_message(message)
        except Exception as e:
            print(e)

    async def on_member_join(self, member):
        await self.main_channel.send(f"Welcome to the server, {member.display_name}")
        if self.db.member_exists(member):
            self.db.set_member_rejoined(member.id)

    async def on_member_remove(self, member):
        await self.main_channel.send(f"*{member.display_name} left the server...*")
        if self.db.member_exists(member):
            self.db.set_member_left(member.id)

    async def on_command_error(self, ctx, error):
        print(f"Command Error: {error}", file=stderr)

        ignored_errors = commands.CommandNotFound
        error = getattr(error, "original", error)

        help_fmt = f"Please see {ctx.prefix}help {ctx.command.name} for details."
        if isinstance(error, ignored_errors):
            return
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Error: You lack the permissions to run this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Error: You're missing a required argument. {help_fmt}")
        elif isinstance(error, (discord.InvalidArgument, commands.UserInputError)):
            await ctx.send(f"Error: You've passed invalid arguments. {help_fmt}")
