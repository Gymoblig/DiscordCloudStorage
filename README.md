# Discord Cloud Storage Bot - Setup Guide

Welcome legend! Here's how to set up your personal Discord Cloud Storage Bot (no coding required).

This version uses a .EXE file, so you don't need to install Python or anything extra. Just follow the steps carefully!

# Step 1: Download the Bot
- Go to the GitHub Releases page of this project.
- Find the latest release.
- Under "Assets", download the provided ZIP file (it will contain a .exe file).
- Extract the ZIP file somewhere safe on your computer (like Desktop or Documents).

# Step 2: Create Your Discord Bot
- Go to https://discord.com/developers/applications
- Click "New Application" → Give it a name (example: StorageBot)
- In the application settings, click on "Bot" tab.
- Click "Add Bot" → Confirm.
- Under "Privileged Gateway Intents", ENABLE:
  - Message Content Intent
  - Server Members Intent
- Click "Reset Token" → Copy the Bot Token (you'll need it soon).

# Step 3: Invite Your Bot to Your Discord Server
- Inside the Developer Portal, go to "OAuth2" → "URL Generator".
- Under "Scopes", select:
  - bot
- Under "Bot Permissions", select:
  - Send Messages
  - Read Message History
  - Manage Messages
  - Attach Files
- Copy the generated URL, open it in your browser.
- Invite the bot to your server.

# Step 4: Get Your Channel ID
- In Discord, go to Settings → Advanced → Enable Developer Mode.
- Right-click on the text channel where you want the bot to store files.
- Click "Copy Channel ID".
- Save it for later.

# Step 5: Prepare Configuration Files
Inside the same folder as your .exe file, create these two files:

1. token.txt
   - Open Notepad.
   - Paste your Discord Bot Token inside.
   - Save the file as token.txt (plain text).

2. config.json
   - Open Notepad again.
   - Paste the following content:

{
  "discord_channel_id": YOUR_CHANNEL_ID
}

- Replace YOUR_CHANNEL_ID with the actual channel ID you copied.
- Save the file as config.json.

Make sure both files are next to your .exe file!

# Step 6: Run the Bot
- Double-click the .exe file.
- A window will open.
- The bot will connect automatically to your Discord server and show your uploaded files.

# Step 7: Use It!
- Click the upload button to upload files.
- Click the download button to download files.
- Click the delete button to delete selected file.
- The bot will automatically split large files into chunks if needed.
- All your files will stay synced across devices through Discord!

# Important Things to Know
- The bot automatically saves file information (metadata) inside Discord, no files are kept locally.
- Even if you change computers, the app will recover everything from the server.
- Very large files (over Discord's limit) will be automatically chunked and uploaded safely.

# Troubleshooting

Problem: Bot does not show online
- Make sure the token.txt file contains the correct bot token.
- Make sure the bot has been invited to your server with the correct permissions.

Problem: Missing config.json or token.txt
- Double-check you created the two required files and saved them in the same folder as the .exe file.

Problem: "No metadata file found" message
- This is normal when starting for the first time. The app will automatically create the metadata file when you upload something.

Problem: App closes instantly
- Open the app from Command Prompt to see if there are any error messages.
- Make sure token.txt and config.json exist and are correct.

# You're All Set!
Congrats, you just built your own Discord-powered Cloud Storage system!

Enjoy your files anywhere, anytime, on any PC! 🔥
