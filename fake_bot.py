from argparse import ArgumentParser

from chat_thief.config.log import logger
from chat_thief.command_parser import CommandParser
from chat_thief.models.user import User
from chat_thief.models.command import Command

DEFAULT_MSG = "!add_perm ha johnnyutah"


def _fake_irc_msg_builder(user, msg):
    return [f":{user}!{user}@user.tmi.twitch.tv", "PRIVMSG", "#beginbot", f":{msg}"]


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--message", "-m", dest="message", default=DEFAULT_MSG)
    parser.add_argument("--user", "-u", dest="user", default="beginbotbot")
    parser.add_argument(
        "--breakpoint", "-b", dest="breakpoint", action="store_true", default=False
    )
    args = parser.parse_args()
    irc_response = _fake_irc_msg_builder(args.user, args.message)

    if args.breakpoint:
        breakpoint()
    elif response := CommandParser(irc_response, logger).build_response():
        print(response)
    else:
        print("No Response")
