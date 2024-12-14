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

Detects Telegram entities posting about crypto coins and forwards this info to an aggregator group,
whilst also forwarding the contract to telegram bot for purchase.

```{bash}
source ./.venv/bin/activate && tg-bot
```

### Find user ids

Run the following command and paste an identifier, i.e. invite link or @username in the prompt.

```{bash}
source ./.venv/bin/activate && get-id-cli
```

### Remote setup

Set up on a remote ubuntu machine as non-root (make sure to have a configuration file ready in home directory):

```{bash}
cd ~ && git clone https://github.com/bobthebuilder887/tgbot && cd tgbot && cp ../config.json . && bash sys/install.sh
```
