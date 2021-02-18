from random import randint
from collections import namedtuple
from datetime import datetime

from discord import Colour, utils

role = namedtuple("Role", ["id", "role_id", "level_unlocked", "colour"])


class Member:
    def __init__(self, bot, discord_member):
        self.bot = bot
        self.db = bot.db
        self.id = discord_member.id
        self.display_name = discord_member.display_name
        self.mention = discord_member.mention
        self.booster = None
        self.level = None
        self.textXP = None
        self.voiceXP = None
        self.avatar = None
        self.colour = None
        self.fetch_data(discord_member)

    def fetch_data(self, discord_member):
        data = self.db.get_member(discord_member)
        for key in data.keys():
            if key == "role":
                pass
            elif key == "booster":
                self.booster = bool(data[key])
            else:
                setattr(self, key, data[key])

        self.colour = self.get_role().colour

    def add_xp(self, xp_type="textXP"):
        boost = 1 if not self.booster else 1.5
        amount = round(randint(10, 25) * boost)
        self.db.add_xp(self.id, amount, xp_type)
        if self.get_xp_threshold() <= self.get_xp() + amount:
            self.db.add_level(self.id)
            return True
        return False

    def add_vc_xp(self):
        self.add_xp(xp_type="voiceXP")

    def get_role(self, role_id=None):
        if not role_id:
            role_id = self.db.get_fields("member", "currentRole", f"id = {self.id}")
            role_data = self.db.get_row("levelRoleReward", f"id = {role_id['currentRole']}")
        else:
            role_data = self.db.get_row("levelRoleReward", f"id = {role_id}")
        if not role_data:
            return None
        colour = Colour(int(role_data["colour"], 16))
        return role(role_data["id"], role_data["roleID"], role_data["levelReq"], colour)

    def get_next_role(self):
        role = self.get_role()
        next_role = self.get_role(role_id=role.id + 1)
        if next_role:
            role = utils.get(self.bot.guild.roles, id=next_role.role_id)
            if not role:
                return "Role Deleted"
            return role.mention
        return "Highest Role!"

    def get_last_reward_time(self):
        data = self.db.get_fields("member", "lastXPReward", f"id = {self.id}")
        return data["lastXPReward"]

    def base_threshold(self, level):
        return 5 * level ** 2 + 50 * level + 100

    def get_xp_threshold(self, level=None):
        xp_jug = 0
        if not level:
            level = self.level + 1
        for idx in range(1, level + 1):
            xp_jug += self.base_threshold(idx)
        return xp_jug

    def get_xp(self):
        return self.textXP + self.voiceXP

    def get_reward_strptime(self):
        return datetime.strptime(self.get_last_reward_time(), "%Y-%m-%d %H:%M:%S")

    def qualifies_for_xp(self):
        current_time = datetime.now()
        stored_time = self.get_reward_strptime()
        return (current_time - stored_time).seconds >= 0

    def get_progress(self):
        level_xp = self.get_level_xp()
        if level_xp == 0:
            return 0
        return round((level_xp / self.get_target()) * 100)

    def get_level_xp(self):
        return self.get_xp() - self.get_xp_threshold(self.level - 1)

    def get_target(self):
        return self.get_xp_threshold() - self.get_xp_threshold(self.level - 1)
