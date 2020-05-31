from tinydb import Query

from chat_thief.models.database import db_table
from chat_thief.prize_dropper import random_soundeffect
from chat_thief.soundeffects_library import SoundeffectsLibrary
from chat_thief.config.log import error, warning, success

from chat_thief.models.command import Command

from chat_thief.models.base_db_model import BaseDbModel

from enum import Enum

# I want these these to be foramt strings
class PurchaseResult(Enum):
    AlreadyOwn = "@{user} already has access to !{sfx}"
    InvalidSFX = "Invalid Effect: {sfx}"
    TooPoor = "@{user} not enough Cool Points to buy !{sfx} - {cool_points}/{cost}"
    SuccessfulPurchase = "@{user} bought !{sfx} for {cost} Cool Points"


class PurchaseReceipt:
    def __init__(self, user, sfx, result, cool_points, cost=None):
        self.user = user
        self.sfx = sfx
        self.cost = cost
        self.cool_points = cool_points
        self.result = result
        self.message = result.value.format(
            user=user, sfx=sfx, cost=cost, cool_points=cool_points
        )

    def __repr__(self):
        return f"PurchaseReceipt({self.user}, {self.sfx}, {self.result.name}, {self.cool_points}, {self.cost})"


class User(BaseDbModel):
    table_name = "users"
    database_path = "db/users.json"

    @classmethod
    def top_three(cls):
        users = [user for user in cls.db().all()]
        top_3 = sorted(users, key=lambda user: user["cool_points"])[-3:]
        top_3.reverse()
        return top_3

    @classmethod
    def all(cls):
        return [user["name"] for user in cls.db().all()]

    @classmethod
    def total_street_cred(cls):
        return sum([user["street_cred"] for user in cls.db().all()])

    @classmethod
    def total_cool_points(self):
        return sum([user["cool_points"] for user in self.db().all()])

    @classmethod
    def richest(cls):
        users = [[user["name"], user["cool_points"]] for user in cls.db().all()]
        return sorted(users, key=lambda user: user[1])

    @classmethod
    def richest_street_cred(cls):
        users = [user for user in cls.db().all()]
        if users:
            return sorted(users, key=lambda user: user["street_cred"])[-1]

    @classmethod
    def richest_cool_points(cls):
        users = [user for user in cls.db().all()]
        if users:
            return sorted(users, key=lambda user: user["cool_points"])[-1]

    @classmethod
    def by_cool_points(cls):
        users = [user for user in cls.db().all()]
        if users:
            return reversed(sorted(users, key=lambda user: user["cool_points"]))

    # ====================================================================

    # We should set self.user here
    def __init__(self, name):
        self.name = name
        self._raw_user = self._find_or_create_user()

    # So this means, when we call, we find or init, thats fine!
    def user(self):
        return self._find_or_create_user()

    def stats(self):
        return f"@{self.name} - Mana: {self.mana()} | Street Cred: {self.street_cred()} | Cool Points: {self.cool_points()}"
        # return f"@{self.name} - Mana: {self.mana()} | Karma: {self.karma()} | Street Cred: {self.street_cred()} | Cool Points: {self.cool_points()}"

    def commands(self):
        return Command.for_user(self.name)

    # Seems like it should be factored away
    def street_cred(self):
        return self.user()["street_cred"]

    def cool_points(self):
        return self.user()["cool_points"]

    def mana(self):
        return self.user()["mana"]

    def update_mana(self, amount):
        return self._update_value("mana", amount)

    # The ride or dies you have
    def karma(self):
        user_result = self.db().search(Query().ride_or_die == self.name)
        return len(user_result)

    def kill(self):
        return self._update_value("mana", -self.mana())

    def revive(self, mana=3):
        return self.set_value("mana", mana)

    def paperup(self, amount=100):
        self.update_street_cred(amount)
        self.update_cool_points(amount)
        return f"@{self.name} has been Papered Up"

    # This also might need a quick exit
    def _find_affordable_random_command(self):
        if self.cool_points() < 1:
            raise ValueError("You can't afford anything!")

        looking_for_effect = True

        while looking_for_effect:
            # Should we update this query to take cost parameter?
            effect = random_soundeffect()
            # We need to check the cost
            command = Command(effect)
            if self.cool_points() >= command.cost() and not command.allowed_to_play(
                self.name
            ):
                looking_for_effect = False
        return command

    def buy_sfx(self, effect):
        current_cool_points = self.cool_points()

        if effect not in SoundeffectsLibrary.fetch_soundeffect_names():
            return PurchaseReceipt(
                user=self.name,
                sfx=effect,
                result=PurchaseResult.InvalidSFX,
                cool_points=current_cool_points,
            )

        command = Command(effect)
        command_cost = command.cost()

        if Command(effect).allowed_to_play(self.name):
            return PurchaseReceipt(
                user=self.name,
                sfx=effect,
                cost=command_cost,
                result=PurchaseResult.AlreadyOwn,
                cool_points=current_cool_points,
            )

        if current_cool_points >= command_cost:
            self.update_cool_points(-command_cost)
            command.allow_user(self.name)
            command.increase_cost()

            return PurchaseReceipt(
                user=self.name,
                sfx=effect,
                cool_points=current_cool_points,
                result=PurchaseResult.SuccessfulPurchase,
                cost=command_cost,
            )
        else:
            return PurchaseReceipt(
                user=self.name,
                sfx=effect,
                cool_points=current_cool_points,
                result=PurchaseResult.TooPoor,
                cost=command_cost,
            )

    # Returning a string with the info
    # of what happened
    def buy(self, effect):
        if effect not in SoundeffectsLibrary.fetch_soundeffect_names():
            raise ValueError(f"Invalid Effect: {effect}")

        if Command(effect).allowed_to_play(self.name):
            return f"@{self.name} already has access to !{effect}"

        current_cool_points = self.cool_points()
        command = Command(effect)
        command_cost = command.cost()

        if current_cool_points >= command_cost:
            self.update_cool_points(-command_cost)
            command.allow_user(self.name)
            command.increase_cost()
            return f"@{self.name} bought !{effect} for {command_cost} Cool Points"
        else:
            return f"@{self.name} not enough Cool Points to buy !{effect} - {current_cool_points}/{command_cost}"

    # This is initial doc
    def doc(self):
        return {
            "name": self.name,
            "street_cred": 0,
            "cool_points": 0,
            "mana": 3,
        }

    def save(self):
        return self._find_or_create_user()

    def _find_or_create_user(self):
        # We should be using get
        user_result = self.db().search(Query().name == self.name)
        if user_result:
            user_result = user_result[0]
            return user_result
        else:
            success(f"Creating New User: {self.doc()}")
            from tinyrecord import transaction

            with transaction(self.db()) as tr:
                tr.insert(self.doc())
            return self.doc()

    def update_cool_points(self, amount=1):
        self._update_value("cool_points", amount)

    def update_street_cred(self, amount=1):
        self._update_value("street_cred", amount)

    def set_ride_or_die(self, ride_or_die):
        if ride_or_die != self.name:
            return self.set_value("ride_or_die", ride_or_die)

    # ===========
    # Punishments
    # ===========

    def remove_all_commands(self):
        for command in self.commands():
            Command(command).unallow_user(self.name)

    def bankrupt(self):
        self.update_street_cred(-self.street_cred())
        self.update_cool_points(-self.cool_points())
        return f"@{self.name} is now Bankrupt"
