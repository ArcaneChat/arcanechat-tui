"""Main UI program"""

import sys
from threading import Thread
from typing import Optional, Tuple

import urwid
from deltachat2 import Client

from .cards_widget import CardsWidget
from .chatlist import CHAT_SELECTED, ChatListWidget
from .composer import SENDING_MSG_FAILED, ComposerWidget
from .addcontact import AddContactWidget
from .container import Container
from .conversation import ConversationWidget
from .eventcenter import CHATLIST_CHANGED, MESSAGES_CHANGED, EventCenter
from .util import shorten_text
from .welcome_widget import WelcomeWidget


class Application:
    """Main application UI"""

    def __init__(self, client: Client, keymap: dict, theme: dict) -> None:
        self.client = client
        self.keymap = keymap
        self.accid: Optional[int] = None
        eventcenter = EventCenter()

        self.chatlist = ChatListWidget(client)
        urwid.connect_signal(eventcenter, CHATLIST_CHANGED, self.chatlist.chatlist_changed)
        chatlist_cont = Container(self.chatlist, self._chatlist_keypress)

        conversation = ConversationWidget(client, theme["background"][-1])
        urwid.connect_signal(self.chatlist, CHAT_SELECTED, conversation.set_chat)
        urwid.connect_signal(eventcenter, MESSAGES_CHANGED, conversation.messages_changed)
        conversation_cont = Container(conversation, self._conversation_keypress)

        composer = ComposerWidget(client, keymap)
        urwid.connect_signal(self.chatlist, CHAT_SELECTED, composer.set_chat)
        composer_cont = Container(composer, self._composer_keypress)

        self.addcontact = AddContactWidget(client, keymap)
        addcontact_cont = Container(self.addcontact, self._addcontact_keypress)

        self.cards = CardsWidget()
        self.cards.add("welcome", WelcomeWidget())
        self.cards.add("conversation", conversation_cont)
        self.cards.show("welcome")

        self.left_side = urwid.Pile([chatlist_cont, (urwid.PACK, addcontact_cont)])
        self.right_side = urwid.Pile([self.cards, (urwid.PACK, composer_cont)])

        vsep = urwid.AttrMap(urwid.Filler(urwid.Columns([])), "separator")

        # layout root
        self.main_columns = urwid.Columns(
            [("weight", 1, self.left_side), (1, vsep), ("weight", 4, self.right_side)]
        )
        self.frame = urwid.Frame(self.main_columns)

        self.loop = urwid.MainLoop(
            urwid.AttrMap(self.frame, "background"),
            [(key, *value) for key, value in theme.items()],
            unhandled_input=self._unhandled_keypress,
        )
        self.loop.screen.set_terminal_properties(colors=256)

        urwid.connect_signal(self.chatlist, CHAT_SELECTED, self.chat_selected)
        urwid.connect_signal(composer, SENDING_MSG_FAILED, self.sending_msg_failed)
        urwid.connect_signal(eventcenter, CHATLIST_CHANGED, self.chatlist_changed)
        urwid.connect_signal(eventcenter, MESSAGES_CHANGED, self.messages_changed)
        client.add_hook(eventcenter.process_core_event)

    def _print_title(self) -> None:
        badge = 0
        for acc in self.client.rpc.get_all_account_ids():
            badge += len(self.client.rpc.get_fresh_msgs(acc))
        name = self.client.rpc.get_config(self.accid, "displayname")
        if not name:
            name = self.client.rpc.get_config(self.accid, "configured_addr")
        name = shorten_text(name, 30)
        if badge > 0:
            text = f"\x1b]2;({badge if badge < 999 else '+999'}) {name}\x07"
        else:
            text = f"\x1b]2;{name}\x07"
        sys.stdout.write(text)

    def exit(self) -> None:
        sys.stdout.write("\x1b]2;\x07")
        raise urwid.ExitMainLoop

    def chat_selected(self, chat: Optional[Tuple[int, int]]) -> None:
        if chat:
            self.cards.show("conversation")
            # focus composer
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        else:
            self.cards.show("welcome")
            # focus chatlist
            self.main_columns.focus_position = 0
            self.left_side.focus_position = 0

    def addcontact_selected(self) -> None:
        self.main_columns.focus_position = 0
        self.left_side.focus_position = 1

    def messages_changed(self, _client: Client, accid: int, chatid: int, _msgid: int) -> None:
        chat = self.chatlist.selected_chat
        if accid == self.accid and chat and chatid in (chat[1], 0):
            self.loop.draw_screen()

    def chatlist_changed(self, _client: Client, accid: int) -> None:
        self._print_title()
        if accid == self.accid:
            self.loop.draw_screen()

    def sending_msg_failed(self, error: str) -> None:
        self.toast(urwid.AttrMap(urwid.Text([" Error: ", error]), "failed"), 5)

    def toast(self, element: urwid.Widget, duration: int) -> None:
        def reset_footer(*_) -> None:
            if self.frame.footer == element:
                self.frame.footer = None

        self.frame.footer = element
        self.loop.set_alarm_in(duration, reset_footer)

    def _unhandled_keypress(self, key: str) -> None:
        if key == self.keymap["addcontact"]:
            self.addcontact_selected()
        if key == self.keymap["quit"]:
            self.exit()

    def _chatlist_keypress(self, _size: list, key: str) -> Optional[str]:
        if key in ("right", "tab"):
            # give focus to the composer area
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
            return None
        return key

    def _conversation_keypress(self, _size: list, key: str) -> Optional[str]:
        if key in ("tab", "esc"):
            # give focus to the composer area
            self.right_side.focus_position = 1
            return None
        return key

    def _composer_keypress(self, _size: list, key: str) -> Optional[str]:
        if key == "esc":
            self.chatlist.select_chat(None)
            return None
        return key

    def _addcontact_keypress(self, _size: list, key: str) -> Optional[str]:
        if key == "esc":
            self.chatlist.select_chat(None)
            return None
        return key

    def run(self, accid: int = 0) -> None:
        rpc = self.client.rpc
        self.accid = accid or self.client.rpc.get_selected_account_id()
        if not self.accid:
            accounts = [rpc.is_configured(accid) for accid in rpc.get_all_account_ids()]
            if accounts:
                self.accid = accounts[0]
            else:
                print("Error: No account configured yet")
                sys.exit(1)
        elif not rpc.is_configured(self.accid):
            print("Error: Account configured yet")
            sys.exit(1)

        self.chatlist.set_account(self.accid)
        self.addcontact.set_accid(self.accid)
        self._print_title()
        Thread(target=self.client.run_forever, daemon=True).start()
        try:
            self.loop.run()
        except KeyboardInterrupt:
            pass
