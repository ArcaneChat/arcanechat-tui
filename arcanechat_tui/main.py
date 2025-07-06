"""Program's entry point"""

import logging
import subprocess

from deltachat2 import Client, CoreEvent, EventType, IOTransport, Rpc, events

from .application import Application
from .cli import Cli
from .logger import create_logger
from .util import get_account

FG_COLOR = "white"
BG_COLOR = "g11"
dtheme = {
    "background": ["", "", "", FG_COLOR, BG_COLOR],
    "status_bar": ["", "", "", "white", "g23"],
    "focused_item": ["", "", "", "white", "g23"],
    "separator": ["", "", "", "g15", "g15"],
    "date": ["", "", "", "#6f0", BG_COLOR],
    "encrypted": ["", "", "", "dark gray", BG_COLOR],
    "unencrypted": ["", "", "", "dark red", BG_COLOR],
    "failed": ["", "", "", "white", "dark red"],
    "selected_chat": ["", "", "", "black", "light blue"],
    "unread_badge": ["", "", "", "#000", "#6f0"],
    "unread_badge_muted": ["", "", "", "#000", "dark gray"],
    "reversed": ["", "", "", BG_COLOR, FG_COLOR],
    "quote": ["", "", "", "dark gray", BG_COLOR],
    "mention": ["", "", "", "bold, light red", BG_COLOR],
    "system_msg": ["", "", "", "dark gray", BG_COLOR],
    "self_msg": ["", "", "", "dark green", BG_COLOR],
}
dkeymap = {
    "quit": "q",
    "addcontact": "+",
    "send_msg": "enter",
    "insert_new_line": "meta enter",
    "next_chat": "meta up",
    "prev_chat": "meta down",
}
hooks = events.HookCollection()


@hooks.on(events.RawEvent)
def log_event(client: Client, accid: int, event: CoreEvent) -> None:
    if event.kind == EventType.INFO:
        client.logger.debug("[acc=%s] %s", accid, event.msg)
    elif event.kind == EventType.WARNING:
        client.logger.warning("[acc=%s] %s", accid, event.msg)
    elif event.kind == EventType.ERROR:
        client.logger.error("[acc=%s] %s", accid, event.msg)


def main() -> None:
    args = Cli().parse_args()
    args.program_folder.mkdir(parents=True, exist_ok=True)
    accounts_dir = args.program_folder / "accounts"
    logging.getLogger("deltachat2.IOTransport").disabled = True
    with IOTransport(accounts_dir=accounts_dir, stderr=subprocess.DEVNULL) as trans:
        client = Client(Rpc(trans), hooks, create_logger(args.log, args.program_folder))
        if "cmd" in args:
            args.cmd(client, args)
        else:
            accid = get_account(client.rpc, args.account)
            Application(client, keymap=dkeymap, theme=dtheme).run(accid)
