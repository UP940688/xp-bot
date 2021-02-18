from sys import stderr
import sqlite3 as sql
from os import path


class DB:
    def __init__(self, name):
        self.name = name
        self.conn = None
        self.cur = None
        self.open(name)

    def open(self, name):
        if not path.exists(name):
            return self.make_database()
        try:
            self.conn = sql.connect(name)
            self.conn.row_factory = sql.Row
            self.cur = self.conn.cursor()
        except sql.Error as e:
            print("Error connecting to database.", file=stderr)

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cur.close()
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def make_database(self):
        self.conn = sql.connect(self.name)
        self.conn.row_factory = sql.Row
        self.cur = self.conn.cursor()
        zero = int(
            input(
                "Database does not exist, creating...\nPlease input ID of role for Level 0 Members:\n> "
            )
        )
        zero_hex = input("Please input hexcode of role 0 colour:\n> ")
        prefix = input("Please enter prefix to use for bot:\n> ")
        self.cur.executescript(
            """
            CREATE TABLE prefix(name TEXT PRIMARY KEY);
            CREATE TABLE levelRoleReward(id INTEGER PRIMARY KEY, roleID INTEGER NOT NULL, levelReq INTEGER NOT NULL, colour TEXT NOT NULL);"""
        )
        self.cur.execute(
            "INSERT INTO levelRoleReward(roleID, levelReq, colour) VALUES (?, 0, ?);",
            (zero, zero_hex),
        )
        self.cur.execue("INSERT INTO prefix(name) VALUES (?)", (prefix,))
        self.cur.executescript(
            """
            CREATE TABLE member(
                id INTEGER PRIMARY KEY,
                booster BOOLEAN NOT NULL DEFAULT 0,
                inServer BOOLEAN NOT NULL DEFAULT 1,
                avatar TEXT,
                textXP INTEGER NOT NULL DEFAULT 0,
                voiceXP INTEGER NOT NULL DEFAULT 0,
                lastXPReward INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
                level INTEGER NOT NULL DEFAULT 0,
                currentRole INTEGER REFERENCES levelRoleReward(id)
            );
            CREATE TRIGGER [CreateMember] AFTER INSERT ON member BEGIN
                UPDATE member SET currentRole = (select id FROM levelRoleReward WHERE levelReq = 0) WHERE id = NEW.id;
            END;
            CREATE TRIGGER [UpdateMemberRole] AFTER UPDATE OF level ON member BEGIN
                UPDATE member SET currentRole = (
                    CASE
                        WHEN level >= (select max(levelReq) from levelRoleReward) THEN
                            currentRole
                        WHEN level >= (select levelReq from levelRoleReward where id = currentRole + 1) THEN
                            currentRole + 1
                        ELSE
                            currentRole
                    END
                ) WHERE id = NEW.id;
            END;
            CREATE TRIGGER [UpdateLastXPReward] AFTER UPDATE OF textXP ON member BEGIN
                UPDATE member SET lastXPReward=CURRENT_TIMESTAMP where id = NEW.id;
            END;"""
        )
        print("Database created. Please manually input any other reward roles into database.")
        self.conn.commit()

    def _get(self, table, cols, condition="", limit=""):
        query = f"SELECT {cols} FROM {table} "
        if condition:
            query += f"WHERE {condition} "
        if limit:
            query += f"LIMIT {limit} "
        self.cur.execute(query)
        rows = self.cur.fetchall()
        if len(rows) == 1:
            return rows[0]
        return rows

    def get_table(self, table):
        return self._get(table, "*")

    def get_row(self, table, condition):
        return self._get(table, "*", condition)

    def get_fields(self, table, fields, condition):
        if not isinstance(fields, str):
            fields = ",".join(fields)
        return self._get(table, fields, condition)

    def get_exists(self, table, id_to_check):
        query = f"SELECT EXISTS(SELECT id FROM {table} WHERE id = ?)"
        self.cur.execute(query, (id_to_check,))
        res = self.cur.fetchall()[0]
        return bool(res[res.keys()[0]])

    def insert(self, table, fields, data):
        if not isinstance(fields, str):
            fields = ",".join(fields)
        if not isinstance(data, str):
            data = ",".join(data)
        query = f"INSERT INTO {table}({fields}) VALUES({data})"
        self.cur.execute(query)
        self.conn.commit()

    def update_field(self, table, table_id, field_to_update, new_value):
        query = f"UPDATE {table} SET {field_to_update} = ? WHERE id = ?"
        self.cur.execute(query, (new_value, table_id))
        self.conn.commit()

    def increment_field(self, table, table_id, field_to_update, amount):
        query = f"UPDATE {table} SET {field_to_update} = {field_to_update} + ? WHERE id = ?"
        self.cur.execute(query, (amount, table_id))
        self.conn.commit()

    def get_prefixes(self):
        prefix_data = self.get_table("prefix")
        prefixes = []
        for prefix in prefix_data:
            prefixes.append(prefix)
        return prefixes

    def add_xp(self, mem_id, amount, xp_type="textXP"):
        self.increment_field("member", mem_id, xp_type, amount)

    def add_level(self, mem_id):
        self.increment_field("member", mem_id, "level", 1)

    def member_exists(self, member):
        return self.get_exists("member", member.id)

    def set_member_left(self, member):
        self.update_field("member", member.id, "inServer", 0)

    def set_member_rejoined(self, member):
        self.update_field("member", member.id, "inServer", 1)

    def insert_member(self, member):
        mem_id = str(member.id)
        booster = str(int(bool(member.premium_since)))
        self.insert("member", "id, booster", [mem_id, booster])

    def get_member(self, member):
        if not self.member_exists(member):
            self.insert_member(member)
        return self.get_row("member", f"id = {member.id}")
