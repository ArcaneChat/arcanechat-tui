"""AddContact area widget"""

from typing import Dict, Optional, Tuple

import urwid
from deltachat2 import Client

from ._version import __version__
from .composer import ReadlineEdit2


class AddContactWidget(urwid.Filler):
    """AddContact area and chat status bar"""

    def __init__(self, client: Client, keymap: Dict[str, str]) -> None:
        self.client = client
        self.keymap = keymap
        self.accid = None
        self.status_bar = urwid.Text(("status_bar", ""), align="left")
        self.edit_widget = ReadlineEdit2(keymap["insert_new_line"])
        prompt = urwid.Columns([(urwid.PACK, urwid.Text("+ ")), self.edit_widget])
        super().__init__(urwid.Pile([urwid.AttrMap(self.status_bar, "status_bar"), prompt]))
        self._update_status_bar(None)

    def set_accid(self, accid: int) -> None:
        self.accid = accid

    def _add_contact(self, text) -> None:
        if self.accid is None:
            return
        # TODO: There should probably be exception handling here.
        contact = self.client.rpc.create_contact(self.accid, text, text)
        result = self.client.rpc.create_chat_by_contact_id(self.accid, contact)

    def _update_status_bar(self, chat: Optional[Tuple[int, int]]) -> None:
        text = f" ArcaneChat {__version__}"
        self.status_bar.set_text(text)

    def keypress(self, size: list, key: str) -> Optional[str]:
        if key == self.keymap["send_msg"]:
            text = self.edit_widget.get_edit_text().strip()
            if text:
                self.edit_widget.set_edit_text("")
                self._add_contact(text)
            return None
        return super().keypress(size, key)
