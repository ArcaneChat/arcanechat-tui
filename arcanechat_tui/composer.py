"""Composer area widget"""

from typing import Dict, Optional, Tuple

import urwid
import urwid_readline
from deltachat2 import Client, JsonRpcError, MsgData

from ._version import __version__
from .util import get_subtitle, shorten_text

SENDING_MSG_FAILED = "sending_msg_failed"


class ReadlineEdit2(urwid_readline.ReadlineEdit):
    """Edit widget"""

    def __init__(self, insert_new_line_key: str) -> None:
        super().__init__(multiline=True)
        del self.keymap["enter"]
        self.keymap[insert_new_line_key] = self.insert_new_line

    def previous_line(self):
        """Patch bug: https://github.com/rr-/urwid_readline/issues/24"""
        x, y = self.get_cursor_coords(self.size)
        return self.move_cursor_to_coords(self.size, x, y - 1)


class ComposerWidget(urwid.Filler):
    """Composer area and chat status bar"""

    signals = [SENDING_MSG_FAILED]

    def __init__(self, client: Client, keymap: Dict[str, str]) -> None:
        self.client = client
        self.keymap = keymap
        self.chat: Optional[Tuple[int, int]] = None
        self.status_bar = urwid.Text(("status_bar", ""), align="left")
        self.edit_widget = ReadlineEdit2(keymap["insert_new_line"])
        prompt = urwid.Columns([(urwid.PACK, urwid.Text("> ")), self.edit_widget])
        super().__init__(urwid.Pile([urwid.AttrMap(self.status_bar, "status_bar"), prompt]))
        self._update_status_bar(None)

    def set_chat(self, chat: Optional[Tuple[int, int]]) -> None:
        self.chat = chat
        self.edit_widget.set_edit_text("")
        self.edit_widget.set_edit_pos(0)
        self._update_status_bar(chat)

    def _send_message(self, text) -> None:
        accid, chatid = self.chat or (0, 0)
        if accid:
            chat = self.client.rpc.get_basic_chat_info(accid, chatid)
            if chat.is_contact_request:
                # accept contact requests automatically on sending
                self.client.rpc.accept_chat(accid, chatid)
            try:
                self.client.rpc.send_msg(accid, chatid, MsgData(text=text))
            except JsonRpcError:
                errmsg = "Message could not be sent, are you a member of the chat?"
                urwid.emit_signal(self, SENDING_MSG_FAILED, errmsg)
        else:
            urwid.emit_signal(self, SENDING_MSG_FAILED, "No chat selected")

    def _update_status_bar(self, chat: Optional[Tuple[int, int]]) -> None:
        if chat:
            info = self.client.rpc.get_basic_chat_info(*chat)
            verified = "✓ " if info.is_self_talk or info.is_device_chat else ""
            muted = " (muted)" if info.is_muted else ""
            name = shorten_text(info.name, 40)

            subtitle = shorten_text(get_subtitle(self.client.rpc, chat[0], info), 40)
            text = f" {verified}[ {name} ]{muted} -- {subtitle}"
        else:
            text = f" ArcaneChat {__version__}"

        self.status_bar.set_text(text)

    def keypress(self, size: list, key: str) -> Optional[str]:
        if key == self.keymap["send_msg"]:
            text = self.edit_widget.get_edit_text().strip()
            if text:
                self.edit_widget.set_edit_text("")
                self._send_message(text)
            return None
        return super().keypress(size, key)
