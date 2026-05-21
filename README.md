# Discord Cloud Storage

Use a Discord text channel as personal cloud storage with folder support.
Files larger than Discord's upload limit are automatically chunked on upload
and reassembled on download. Drag entire folders and their structure is
preserved. The UI and the bot launch together in one Python process.

---

## Features

- Black and white CustomTkinter UI with responsive grid of file cards
- Full folder support: create folders, drag-drop folders, navigate via breadcrumb
- Drag and drop files or folders anywhere on the window to upload
- Automatic chunking (default 25 MB per chunk, matching Discord's bot file limit)
- Metadata stored as a pinned JSON attachment in the channel (nothing local, recoverable on any device)
- Upload, download, delete files and folders
- Search across all files regardless of current folder
- Double-click folder cards to navigate inside

---

## Requirements

- Python 3.10 or newer
- A Discord bot with Message Content Intent enabled
- A dedicated text channel on your Discord server

---

## Setup

### 1. Install dependencies

```
pip install -r requirements.txt
```

On Windows the tkinterdnd2 wheel includes the Tcl extension. On Linux you
may also need: `sudo apt install python3-tk`.

### 2. Create the Discord bot

1. Go to https://discord.com/developers/applications
2. New Application, give it a name (e.g. StorageBot)
3. Open the Bot tab, click Add Bot
4. Under Privileged Gateway Intents enable Message Content Intent
5. Click Reset Token and copy the bot token

### 3. Invite the bot

In OAuth2, URL Generator:

- Scopes: bot
- Bot permissions: Send Messages, Read Message History, Manage Messages, Attach Files

Open the generated URL and add the bot to your server.

### 4. Get the channel ID

In Discord go to Settings, Advanced, enable Developer Mode. Then right-click
the text channel you want to use as storage and choose Copy Channel ID.

### 5. Configuration files

Both files must sit in the same folder as main.py:

token.txt - you must create this file yourself. Open Notepad (or any text
editor), paste your bot token on a single line with no quotes, and save it as
token.txt in the project folder.

config.json - already provided as a template:

```json
{
    "discord_channel_id": 123456789012345678,
    "chunk_size_mb": 25
}
```

Replace the channel ID with your own.

### 6. Run

```
python main.py
```

The window opens and the bot connects automatically. The status dot in the
top-right corner turns white once the bot is ready.

---

## Usage

- Press "+ Upload" to pick files, or drag them into the window
- Drag an entire folder to upload it recursively (structure is preserved)
- Press "+ Folder" to create an empty folder
- Click folder cards to navigate inside, use the breadcrumb to go back
- Search filters across all files regardless of folder
- Press Refresh to re-fetch metadata from Discord

---

## Configuration

- chunk_size_mb: maximum chunk size in megabytes. Default 25. Drop to 8 for
  extra safety on old servers or raise to 50/100 for Boost Level 2/3 servers.
- discord_channel_id: the numeric ID of the text channel used for storage.

---

## How it works

1. Files are split into chunks up to chunk_size_mb each.
2. Each chunk is posted as an attachment in the Discord channel.
3. A pinned message holds a JSON file (cloudstorage_metadata.json) that maps
   file names, paths, sizes, and chunk message IDs.
4. On download the app fetches each chunk message, reads the attachment, and
   reassembles the file locally.
5. Folders are virtual: they exist as path prefixes on files plus an explicit
   folder list for empty directories.

---

## Troubleshooting

- Window opens but bot stays on "Connecting..." - check the token and that the
  bot has been invited with correct permissions.
- "Configured channel is not a text channel" - verify the channel ID points to
  a regular text channel, not voice/category/forum.
- Upload errors at large files - the server's boost tier limits attachment size.
  Lower chunk_size_mb in config.json.
- Metadata pin missing - if someone accidentally deleted the pinned message,
  chunk messages still exist in the channel but the index is lost. Re-uploading
  will start fresh metadata.

---

## Project structure

```
main.py          Entry point, loads config, starts bot + UI
bot.py           discord.py client in a background thread
storage.py       Chunking, path helpers, folder enumeration
metadata.py      Metadata model and Discord persistence
ui/
  app.py         Main window, toolbar, breadcrumb, grid
  card.py        FileCard and FolderCard widgets
  icons.py       Icon loader with auto-generated folder icon
  theme.py       Black and white color tokens
icons/           PNG icons by file type
config.json      Channel ID and chunk size
token.txt        Bot token (git-ignored)
```
