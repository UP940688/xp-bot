import discord
from discord.ext import commands
import config as CONFIG


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Shows prefixes for bot.")
    async def prefix(self, ctx):
        """Show the prefixes that the bot will respond to."""
        prefixes = self.bot.command_prefix(self.bot)
        del prefixes[0]
        await ctx.send("Valid prefixes for this bot are:" + ", ".join(prefixes))

    @commands.command(name="help", aliases=["commands"], brief="Displays this help message.")
    async def help_command(self, ctx, cog_cmd=None):
        """Displays this help message.
        Optionally takes name of Cog or Command to display help about"""

        embed = discord.Embed()
        embed.colour = discord.Colour(0xF10057)
        all_cogs = [c for c in sorted(self.bot.cogs.keys())]
        all_commands = []

        for cog in all_cogs:
            cog_commands = self.bot.get_cog(cog).get_commands()
            for command in cog_commands:
                try:
                    if command.hidden and not await command.can_run(ctx):
                        continue
                except:
                    continue
                all_commands.append(command.name)

        if cog_cmd is None:
            help_cogs = all_cogs
        elif cog_cmd not in all_cogs and cog_cmd not in all_commands:
            return await ctx.send("Invalid cog/command specified.\n")
        elif cog_cmd in all_cogs:
            help_cogs = [self.bot.get_cog(cog_cmd).qualified_name]
        else:
            help_cogs = []

        if len(help_cogs) == 0:
            help_command = self.bot.get_command(cog_cmd)
            embed.add_field(name=help_command.name, value=f"{help_command.help}", inline=False)
            return await ctx.send(embed=embed)

        embed.add_field(
            name="Command Help",
            value=f"Type {ctx.prefix}help command for a description of a specific command",
        )

        for each_cog in help_cogs:
            new_commands = sorted(
                self.bot.get_cog(each_cog).get_commands(), key=lambda c: c.qualified_name
            )
            command_fmt = ""
            for each_command in new_commands:
                try:
                    if each_command.hidden and not await each_command.can_run(ctx):
                        print("can't run")
                    else:
                        command_fmt += f"`{each_command.name}` "
                except Exception as e:
                    print(f"exception occured: {e}")
            if command_fmt:
                embed.add_field(name=each_cog, value=command_fmt, inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="reload", hidden=True)
    @commands.is_owner()
    async def reload_cogs(self, ctx):
        num = 0
        for cog in CONFIG.COGS:
            try:
                self.bot.unload_extension(cog)
                self.bot.load_extension(cog)
                num += 1
            except Exception as e:
                await ctx.send(f"Had issues reloading cog: {e}")
        await ctx.send(f"{num}/{len(self.bot.cogs)} cogs reloaded.")


def setup(bot):
    bot.add_cog(Help(bot))
