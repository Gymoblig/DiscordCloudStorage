# Discord Cloud Storage

Use a Discord text channel as personal cloud storage. Files larger than the
Discord upload limit are automatically chunked on upload and reassembled on
download. The UI and the bot run together in one Python process.

## Features

- Sleek black & white CustomTkinter UI with a grid of file cards
- Drag & drop files anywhere on the window to upload
- Automatic chunking (default 25 MB per chunk, Discord's bot file limit)
- Metadata stored as a pinned JSON message in the same channel - nothing local,
  recoverable on any device
- Upload, download, delete, search, refresh

## Setup

### 1. Python

Requires Python 3.10+. Install dependencies:

```
pip install -r requirements.txt
```

On Windows the `tkinterdnd2` wheel ships with the required Tcl extension. On
Linux you may also need: `sudo apt install python3-tk`.

### 2. Discord bot

1. Go to <https://discord.com/developers/applications>
2. New Application -> give it a name (e.g. `StorageBot`)
3. Open the **Bot** tab, click **Add Bot**
4. Under **Privileged Gateway Intents** enable **Message Content Intent**
5. Click **Reset Token** and copy the bot token

### 3. Invite the bot

In **OAuth2 -> URL Generator**:

- Scopes: `bot`
- Bot permissions: `Send Messages`, `Read Message History`, `Manage Messages`,
  `Attach Files`

Open the generated URL and add the bot to your server.

### 4. Channel ID

In Discord: Settings -> Advanced -> enable **Developer Mode**, then right-click
your storage channel and choose **Copy Channel ID**.

### 5. Config files

Next to `main.py`:

- `token.txt` - paste the bot token (single line, no quotes)
- `config.json` - already provided as a template:

```json
{
  "discord_channel_id": 123456789012345678,
  "chunk_size_mb": 25
}
```

### 6. Run

```
python main.py
```

The UI starts and the bot logs in automatically. When the dot in the top right
turns white the bot is connected.

## Notes

- Chunk size defaults to 25 MB (Discord's default upload limit for bots on
  non-boosted servers). Drop to `8` for extra safety margin on old servers, or
  raise to `50` / `100` if your server has Boost Level 2 / 3.
- Metadata is stored as the only pinned message containing
  `cloudstorage_metadata.json`. Don't delete the pin.
- The token in `token.txt` stays on your machine. `.gitignore` excludes it.

## Troubleshooting

- **Window opens but bot stays "Connecting..."** - check the token and that the
  bot has been invited to the server with the right permissions.
- **"Configured channel is not a text channel"** - double-check the channel ID
  is the right one (text channel, not voice/category/forum).
- **Upload errors at large files** - Discord rejects attachments above the
  server's tier limit. Lower `chunk_size_mb` in `config.json`.
