# User Guide

## Installation

Install ArcaneChat TUI with pip:

```
$ pip install -U arcanechat-tui
```

## Usage

After installation the command `arcanechat` should be available, or you can use
`python3 -m arcanechat-tui`. You can check if it is installed running the command
`arcanechat --version` or `arcanechat --help` to see all the options

### Creating new account

The first time you use ArcaneChat TUI you need to configure your account:

```
$ arcanechat init me@example.com MyPassword
```

Then run `arcanechat` command to start the application with your configured account.

### Opening accounts from other Delta Chat clients

If you want to use an already existent account, for example to open an account from
the official Delta Chat client:

```
$ arcanechat -f ~/.config/DeltaChat/
```

## Tips

- The message timestamp will be gray if the message is encrypted, or red it is not encrypted.
- You will see `→` in your message if it is not sent yet, `✓` if it was send,
  `✓✓` when the message was read, or a red `!` if the message was not delivered to some of
  the recipients.
- If you like to use the mouse, you can use the mouse to select chats in the chat list,
  select the draft area or scroll in the message history.

## Default Shortcuts

- Press <kbd>Esc</kbd> in the draft/composer area to close the chat and go to the chat list.
- Press <kbd>q</kbd> to quit the program.
- Press <kbd>+</kbd> in the chat list to add a new chat by e-mail address.
- Use <kbd>Meta</kbd> + <kbd>Enter</kbd> to enter new line.
- For shortcuts in the draft/composer area see: [urwid_readline](https://github.com/rr-/urwid_readline)
