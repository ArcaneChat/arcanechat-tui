import os
import subprocess
import sys
from typing import Optional

import urwid
from deltachat import Chat, Message, account_hookimpl
from emoji import emojize

from .event import AccountPlugin, ChatListMonitor
from .notifications import notify_msg
from .util import COMMANDS, Container, is_multiuser
from .widgets.chatlist import ChatListWidget
from .widgets.composer import ComposerWidget
from .widgets.conversation import ConversationWidget


class Application(ChatListMonitor):
    def __init__(
        self,
        conf: dict,
        keymap: dict,
        theme: dict,
        app_name: str,
        events: AccountPlugin,
    ) -> None:
        self.conf = conf
        self.keymap = keymap
        self.app_name = app_name
        self.events = events

        account = self.events.account
        palette = [
            ("bg", *theme["background"]),
            ("status_bar", *theme["status_bar"]),
            ("separator", *theme["separator"]),
            ("date", *theme["date"]),
            ("encrypted", *theme["encrypted"]),
            ("unencrypted", *theme["unencrypted"]),
            ("cur_chat", *theme["cur_chat"]),
            ("reversed", *theme["reversed"]),
            ("quote", *theme["quote"]),
            ("mention", *theme["mention"]),
            ("self_msg", *theme["self_msg"]),
            ("unread_chat", *theme["unread_chat"]),
            ("system_msg", *theme["system_msg"]),
            ("failed", *theme["failed"]),
        ]
        display_emoji = conf["global"]["display_emoji"]

        # Chatlist
        chatlist_widget = ChatListWidget(keymap, self.events.select_chat, display_emoji)
        self.events.add_chatlist_monitor(chatlist_widget)
        chatlist_container = Container(chatlist_widget, self._chatlist_keypress)

        # Conversation messages
        conversation_widget = ConversationWidget(
            conf["global"]["date_format"], keymap, theme, account, display_emoji
        )
        self.events.add_chatlist_monitor(conversation_widget)
        conversation_container = Container(
            conversation_widget, self._conversation_keypress
        )

        # message writing + status bar widget
        self.composer = ComposerWidget(keymap, display_emoji)
        self.events.add_chatlist_monitor(self.composer)
        composer_container = Container(
            self.composer, self._composer_keypress, process_unhandled=True
        )

        # Right pannel
        self.right_side = urwid.Pile([conversation_container, (2, composer_container)])

        vert_separator = urwid.AttrMap(urwid.Filler(urwid.Columns([])), "separator")

        # Final arrangements
        self.main_columns = urwid.Columns(
            [
                ("weight", 1, chatlist_container),
                (1, vert_separator),
                ("weight", 4, self.right_side),
            ]
        )

        self.events.add_chatlist_monitor(self)
        account.add_account_plugin(self)

        bg = urwid.AttrMap(self.main_columns, "bg")
        self.main_loop = urwid.MainLoop(
            bg,
            palette,
            unhandled_input=self._unhandle_key,
            screen=urwid.raw_display.Screen(),
        )
        self.main_loop.screen.set_terminal_properties(colors=256)

    def run(self) -> None:
        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            try:
                self.exit()
            except urwid.ExitMainLoop:
                pass

    def exit(self) -> None:
        if self.events.current_chat:
            self.composer.save_draft()
        sys.stdout.write("\x1b]2;\x07")
        raise urwid.ExitMainLoop

    def chatlist_changed(self, current_chat_index: Optional[int], chats: list) -> None:
        self._print_title(self.events.account.get_fresh_messages_cnt())

        if hasattr(self, "main_loop"):
            self.main_loop.draw_screen()

    def chat_selected(self, index: Optional[int], chats: list) -> None:
        self.main_columns.focus_position = 2
        self.right_side.focus_position = 1

    @account_hookimpl
    def ac_incoming_message(self, message: Message) -> None:
        if not self.conf["global"]["notification"]:
            return

        sender = message.get_sender_contact()
        acc = self.events.account
        me = acc.get_self_contact()
        if sender == me:
            return

        notify = not message.chat.is_muted()
        if not notify and is_multiuser(message.chat):
            if message.quote and message.quote.get_sender_contact() == me:
                notify = True
            else:
                name = acc.get_config("displayname") or me.addr
                notify = f"@{name}" in message.text
        if notify:
            notify_msg(message)

    def _print_title(self, messages_count: int) -> None:
        if messages_count > 0:
            text = f"\x1b]2;{self.app_name} ({messages_count})\x07"
        else:
            text = f"\x1b]2;{self.app_name}\x07"
        sys.stdout.write(text)

    def _unhandle_key(self, key: str) -> None:
        if key == self.keymap["quit"]:
            self.exit()
        elif key == self.keymap["toggle_chatlist"]:
            # check if already hidden
            if self.main_columns.contents[0][1][1] == 1:
                cols_contents = self.main_columns.contents
                # hidding
                cols_contents[0] = (cols_contents[0][0], ("given", 0, False))
                cols_contents[1] = (cols_contents[1][0], ("given", 0, False))
            else:
                self.main_columns.contents[0] = (
                    self.main_columns.contents[0][0],
                    ("weight", 1, True),
                )
                self.main_columns.contents[1] = (
                    self.main_columns.contents[1][0],
                    ("given", 1, False),
                )
                self.main_columns.focus_position = 0
        elif key == self.keymap["prev_chat"]:
            self.events.select_previous_chat()
        elif key == self.keymap["next_chat"]:
            self.events.select_next_chat()
        elif key == self.keymap["insert_text"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        elif key == self.keymap["open_file"]:
            if not self.conf["global"]["open_file"]:
                return
            current_chat = self.events.current_chat
            if current_chat:
                msgs = current_chat.get_messages()
                if msgs:
                    for msg in reversed(msgs[-20:]):
                        if msg.filename:
                            subprocess.Popen(  # noqa
                                ["xdg-open", msg.filename],
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                            )
                            break

    def _chatlist_keypress(self, _size: list, key: str) -> Optional[str]:
        if key == self.keymap["right"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        elif key == self.keymap["toggle_chatlist"]:
            self.main_columns.focus_position = 2
            self.right_side.focus_position = 1
        else:
            return key
        return None

    def _conversation_keypress(self, _size: list, key: str) -> Optional[str]:
        if key == self.keymap["left"]:
            self.main_columns.focus_position = 0
            return None
        return key

    def _composer_keypress(self, size: list, key: str) -> Optional[str]:
        # send message
        if key == self.keymap["send_msg"]:
            edit = self.composer.widgetEdit
            text = edit.get_edit_text().strip()
            if not text:
                return None
            current_chat = self.events.current_chat
            if text.startswith("//"):
                text = text[1:]
            elif text.startswith("/"):
                edit.set_edit_text("")
                text = self._process_command(current_chat, text)
                if text:
                    edit.set_edit_text(text)
                edit.set_edit_pos(len(edit.get_edit_text()))
                self._resize_zone(size)
                return None
            if current_chat.is_contact_request():
                # accept contact requests automatically until UI allows to accept/block
                current_chat.accept()
            try:
                current_chat.send_text(emojize(text))
                edit.set_edit_text("")
            except ValueError:
                edit.set_edit_text(
                    "Error: message could not be sent, are you a member of the chat?"
                )
            edit.set_edit_pos(len(edit.get_edit_text()))
            self._resize_zone(size)
        # give the focus to the chat list
        elif key == self.keymap["left"]:
            self.main_columns.focus_position = 0
        # give the focus to the message list
        elif key in ("up", "page up", "esc"):
            self.right_side.focus_position = 0
        else:
            self._resize_zone(size)
            return key
        return None

    def _process_command(self, chat: Chat, cmd: str) -> str:
        model = self.events
        acc = model.account
        args = cmd.split(maxsplit=1)

        text = ""
        if args[0] == COMMANDS["/query"]:
            try:
                chat = acc.create_chat(args[1].strip())
                model.select_chat_by_id(chat.id)
            except AssertionError:
                text = "Error: invalid email address"
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/join"]:
            chat = acc.create_group_chat(args[1].strip())
            model.select_chat_by_id(chat.id)
        elif args[0] == COMMANDS["/delete"]:
            model.current_chat.delete()
            model.select_chat(None)
        elif args[0] == COMMANDS["/names"]:
            text = "\n".join(c.addr for c in model.current_chat.get_contacts())
        elif args[0] == COMMANDS["/add"]:
            try:
                for addr in args[1].split(","):
                    model.current_chat.add_contact(addr.strip())
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/kick"]:
            try:
                for addr in args[1].split(","):
                    model.current_chat.remove_contact(addr.strip())
            except AttributeError:
                text = "Error: invalid email address"
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/part"]:
            try:
                model.current_chat.remove_contact(acc.get_self_contact())
            except ValueError as ex:
                text = f"Error: {ex}"
        elif args[0] == COMMANDS["/id"]:
            text = str(model.current_chat.id)
        elif args[0] == COMMANDS["/send"]:
            try:
                path = os.path.expanduser(args[1].strip())
                chat.send_msg(chat.account.create_message(filename=path))
            except ValueError as ex:
                text = f"Error: {ex}"
        else:
            text = f"ERROR: Unknown command {args[0]}"

        return text

    def _resize_zone(self, size: list) -> None:
        text_caption = self.composer.text_caption
        text = self.composer.widgetEdit.get_edit_text()
        rows_needed = 1
        for line in text.split("\n"):
            rows_needed += int((len(line) + len(text_caption)) / size[0]) + 1
        rows_needed = min(rows_needed, 10)
        contents = self.right_side.contents
        if rows_needed != size[1]:
            contents[1] = (contents[1][0], ("given", rows_needed))
