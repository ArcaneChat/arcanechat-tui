# ArcaneChat TUI

[![Latest Release](https://img.shields.io/pypi/v/arcanechat-tui.svg)](https://pypi.org/project/arcanechat-tui)
[![License](https://img.shields.io/pypi/l/arcanechat-tui.svg)](https://pypi.org/project/arcanechat-tui)
[![CI](https://github.com/ArcaneChat/arcanechat-tui/actions/workflows/python-ci.yml/badge.svg)](https://github.com/ArcaneChat/arcanechat-tui/actions/workflows/python-ci.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> a lightweight ArcaneChat client for the command line

<p align="center">
  <img src="https://github.com/ArcaneChat/arcanechat-tui/blob/main/screenshots/e1.png?raw=true" alt="screenshot of ArcaneChat"/>
</p>

ArcaneChat TUI is a ncurses Delta Chat client developed in Python with the urwid library.

#### Features

- [X] Create accounts
- [X] Tweak account configuration (ex. set display name and status)
- [X] Ability to send text messages :)
- [X] Read receipts ✓✓
- [X] Display quoted messages
- [ ] Account switcher
- [ ] Chat operations: delete, pin/unpin, mute/unmute, archive/unarchive, add/remove members, etc.
- [ ] Message operations: reply, delete, open attachment/links, see info, jump to quote
- [ ] Import/export keys and backups
- [ ] Ability to send files
- [ ] Notifications
- [ ] Support for contact verification and group invitations links
- [ ] Block/unblock contacts and see the list of blocked contacts
- [ ] See contact list
- [ ] Search messages and chats
- [ ] Open HTML messages
- [ ] View archived chats

## Installing

#### With pip

This program depends on the `deltachat-rpc-server` program to be installed in your system,
if you want to try to install it using pip run:

```
$ pip install -U "arcanechat-tui[full]"
```

If you will manually install the `deltachat-rpc-server` program in
your PATH on your own, then run:

```
$ pip install -U arcanechat-tui
```

#### With pipx

To install ArcaneChat TUI with [pipx](https://pipx.pypa.io):

```
$ pipx install arcanechat-tui deltachat-rpc-server
```

## Using

After installation the command `arcanechat-tui`
(and `arcanechat` alias) should be available.

For more tips and info check [the user guide](https://github.com/ArcaneChat/arcanechat-tui/blob/main/docs/user-guide.md)
