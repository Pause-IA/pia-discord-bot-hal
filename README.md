# PIA Discord Bot

A Discord bot that monitors channels for specific links, creates threads, fetches content, summarizes it using an LLM, and posts the summaries to both Discord and a Coda table.

## Features

- Monitors Discord channels for links to specific websites (YouTube, Twitter, etc.)
- Creates threads for detected links
- Fetches content information from the links
- Summarizes content using an LLM
- Posts summaries to Discord and a Coda table
- Optionally creates a thread for every message posted in chosen channels
  (`discord.auto_thread_channels`, see below)

## Setup

1. Clone this repository
2. Install dependencies
3. Configure the bot in \pia-discord-bot_config.json\
4. Run the bot with \python pia-discord-bot.py\

## Configuration

See \pia-discord-bot_config.json\ for configuration options.

### Automatic threads

List channel IDs in `discord.auto_thread_channels` to give every new message
posted there its own thread, named after the message's first line (links and
Markdown removed, 100 characters at most). Messages from bots, system messages
and `!pia` commands are skipped. A message whose supported link (video) is
summarised in a monitored channel keeps a single thread, the summary's. An
empty or missing list leaves the feature off. The bot needs the *Create Public
Threads* permission in those channels.

Tests: `python -m unittest discover -s tests`.

## License

[MIT](https://choosealicense.com/licenses/mit/)
