"""Utilities"""

from pathlib import Path
from typing import Any

from deltachat2 import ChatType, Rpc


def shorten_text(text: str, width: int, placeholder: str = "…") -> str:
    text = " ".join(text.split())
    if len(text) > width:
        width -= len(placeholder)
        assert width > 0, "placeholder can't be bigger than width"
        text = text[:width].strip() + placeholder
    return text


def get_subtitle(rpc: Rpc, accid: int, chat: Any) -> str:
    if chat.is_self_talk:
        return "Messages I sent to myself"
    if chat.is_device_chat:
        return "Locally generated messages"
    if chat.chat_type == ChatType.MAILINGLIST:
        return "Mailing List"
    if chat.chat_type == ChatType.IN_BROADCAST:
        return "Channel"

    members = rpc.get_chat_contacts(accid, chat.id)
    if chat.chat_type == ChatType.SINGLE:
        subtitle = rpc.get_contact(accid, members[0]).address
    elif chat.chat_type == ChatType.OUT_BROADCAST:
        count = len(members)
        subtitle = "1 subscribers" if count == 1 else f"{count} subscribers"
    else:
        count = len(members)
        subtitle = "1 member" if count == 1 else f"{count} members"

    return subtitle


def abspath(path: str) -> Path:
    try:
        return Path(path).expanduser().absolute()
    except RuntimeError:
        return Path(path).absolute()


def parse_docstring(txt) -> tuple:
    """parse docstring, returning a tuple with short and long description"""
    description = txt
    i = txt.find(".")
    if i == -1:
        help_ = txt
    else:
        help_ = txt[: i + 1]
    return help_, description


def get_or_create_account(rpc: Rpc, addr: str) -> int:
    """Get account for address, if no account exists create a new one."""
    accid = get_account(rpc, addr)
    if not accid:
        accid = rpc.add_account()
        rpc.set_config(accid, "addr", addr)
    return accid


def get_account(rpc: Rpc, addr: str) -> int:
    """Get account id for address.
    If no account exists with the given address, zero is returned.
    """
    if not addr:
        return 0

    try:
        return int(addr)
    except ValueError:
        for accid in rpc.get_all_account_ids():
            if addr == get_address(rpc, accid):
                return accid

    return 0


def get_address(rpc: Rpc, accid: int) -> str:
    if rpc.is_configured(accid):
        return rpc.get_config(accid, "configured_addr")
    return rpc.get_config(accid, "addr")
