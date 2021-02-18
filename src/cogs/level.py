import discord
from discord.ext import commands, tasks
import datetime

from datatypes import member


class LevelUpEmbed:
    def __init__(self, mem, channel):
        self.member = mem
        self.channel = channel
        level = self.member.level

        self.embed = discord.Embed(title="Congratulations! You've leveled up!")
        self.embed.description = f"Hey {mem.mention}! Well done on reaching level {level+1}"
        self.embed.colour = self.member.colour

    async def send(self):
        await self.channel.send(embed=self.embed)


class Level(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db
        self.loop_check_vc.start()

    @tasks.loop(minutes=10.0)
    async def loop_check_vc(self):
        await self.check_vc()

    @loop_check_vc.before_loop
    async def before_check_vc(self):
        await self.bot.wait_until_ready()

    async def add_member_xp(self, mem):
        level_up = mem.add_xp()
        if level_up:
            embed = LevelUpEmbed(mem, self.bot.level_up_channel)
            await embed.send()

    async def check_vc(self):
        candidates = []
        for vc in self.bot.guild.voice_channels:
            humans = [m for m in vc.members if not m.bot]
            if len(humans) >= 2:
                candidates += humans

        for c in candidates:
            if c.voice.mute or c.voice.self_mute or c.voice.afk:
                continue
            mem = member.Member(self.bot, mem)
            await self.add_member_xp(mem)

    async def process_message(self, message):
        mem = member.Member(self.bot, message.author)
        if mem.qualifies_for_xp():
            await self.add_member_xp(mem)

    @commands.command(name="level", aliases=["lvl", "profile"])
    async def get_level(self, ctx, d_mem: discord.Member = None):
        if not d_mem:
            d_mem = ctx.message.author
        mem = member.Member(self.bot, d_mem)
        embed = discord.Embed(title=f"Level & XP Information ({d_mem.display_name})")
        embed.colour = mem.get_role().colour
        embed.set_thumbnail(url=d_mem.avatar_url)
        titles = [
            "Level",
            "Text XP",
            "Voice XP",
            f"Progress ({mem.get_progress()}%)",
            "Next Reward",
            "Booster",
        ]
        booster = "Yes!" if mem.booster else "No :c"
        # add one to prevent division-by-zero error
        values = [
            mem.level,
            mem.textXP,
            mem.voiceXP,
            f"{round(mem.get_level_xp()+1):,}/{mem.get_target():,}",
            mem.get_next_role(),
            booster,
        ]
        for idx, title in enumerate(titles):
            embed.add_field(name=title, value=values[idx])
        await ctx.send(embed=embed)

    @commands.command(name="xp")
    async def get_timeout(self, ctx, d_mem: discord.Member = None):
        if not d_mem:
            d_mem = ctx.message.author
        mem = member.Member(self.bot, d_mem)
        embed = discord.Embed(title=f"XP Information ({d_mem.display_name})")
        embed.colour = mem.get_role().colour
        embed.set_thumbnail(url=d_mem.avatar_url)
        time = mem.get_reward_strptime()
        next_time = time + datetime.timedelta(minutes=3)
        embed.description = f"""Text XP: {mem.textXP}
Voice XP: {mem.voiceXP}
Next qualifies for XP: {next_time.hour}:{next_time.minute}"""
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Level(bot))
