# Telegram Tools

Tools for tracking users and buying their coins.

## Requirements

- Python3.12
- Telegram user API key. See [https://core.telegram.org/api/obtaining_api_id](https://core.telegram.org/api/obtaining_api_id)

## Install

Uses python's built-in virtual environment

### Basic

```{bash}
make install
```

### Dev

```{bash}
make install_dev
```

## Usage

Before running the bot, set up the `config.json` file. Use `config.json.example` as a template.

### Main bot

Detects users posting Solana and EVM contracts, which get forwarded to an aggregator group. If the contract is never seen before it gets forwarded to a buy bot. There are two main strategies which can be toggled using the config:

1. Buy bot #1 buys new contracts posted at a specified time frame
2. Buy bot #2 buys new contracts posted by white-listed users

```{bash}
source ./.venv/bin/activate && tg_bot
```

### Find user ids

Run the following command and paste an identifier, i.e. invite link or @username in the prompt.

```{bash}
source ./.venv/bin/activate && get-id-cli
```

### Remote setup

Set up on a remote ubuntu machine as non-root (make sure to have a configuration file ready in home directory):

```{bash}
cd ~ && git clone https://github.com/bobthebuilder887/tgbot && cd tgtools && cp ../config.json . && bash sys/install.sh
```
