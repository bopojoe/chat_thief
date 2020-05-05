from chat_thief.models.user import User
from chat_thief.models.command import Command
from chat_thief.config.stream_lords import STREAM_GODS

from chat_thief.soundeffects_library import SoundeffectsLibrary


class CommandSharer:
    def __init__(self, user, command, friend):
        self.user = user
        self.command = command
        self.friend = friend

    def share(self):
        if not self.command in SoundeffectsLibrary.fetch_soundeffect_names():
            raise ValueError(f"!{self.command} invalid command")

        command = Command(name=self.command)

        if self.user in STREAM_GODS:
            perm_result = command.allow_user(self.friend)
            return f"{self.user} shared {perm_result}"
        elif User(self.user).street_cred() > 0:
            perm_result = command.allow_user(self.friend)
            if perm_result:
                print("\nWe have a Perm Result")
                User(self.user).remove_street_cred()
                # sharing and stealing both should double
                command.increase_cost(command.amount() * 2)
                # We Need to increase the cost
                return f"{self.user} shared {perm_result}"
            else:
                print("\nWe NOOOOO have a Perm Result")
                return f"{self.user} cannot add permissions"
        else:
            return f"@{self.user} Not enough street_cred to share !{self.command} with @{self.friend}"
