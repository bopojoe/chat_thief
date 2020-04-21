from chat_thief.permissions_manager import PermissionsManager
from chat_thief.user import User

class CommandGiver:
    def __init__(self, user, command, friend):
        self.user = user
        self.command = command
        self.friend = friend

    def share(self):
        # We need to remove the permissions for the user
        perm_result = PermissionsManager(
            user=self.user, command=self.command, args=[self.command, self.friend],
        ).swap_perm(self.user)

        if perm_result:
            print("\nWe have a Perm Result")
            User(self.user).remove_street_cred()
            return perm_result
        else:
            print("\nWe NOOOOO have a Perm Result")
            return f"{self.user} cannot add permissions"
