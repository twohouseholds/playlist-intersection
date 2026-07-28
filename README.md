# Playlist Intersection

Tool to create an intersection playlist with the common tracks of a number of playlists (as Spotify currently does not support this).

## Setup

1. Clone the repository.
2. Install Python 3.12 or newer.
3. Install `uv` (e.g., via `winget install --id=astral-sh.uv  -e`).
4. Switch to the directory of your clone and run `uv sync --all-packages`.
5. Rename `.env.template` to `.env` and enter your Spotify Web API credentials:
   1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   2. Create an app with the `Redirect URIs` set to `http://127.0.0.1:8888/callback` and `Which API/SDKs are you planning to use?` set to `Web API`.
   3. Copy the `Client ID` and `Client Secret` to the respective environment variables in `.env`.
6. Run the script: `uv run --env-file .env python scripts/playlist_intersection.py`.
   - The first time you run the script, a browser popup will ask you to confirm you want to grant the necessary permissions to run the script.
   - If the script fails with `403 Forbidden` for a playlist that you can access via Spotify UI, try using a personal copy: Go to the playlist -> three dots -> `Add to other playlist` -> `New playlist`. Now use the link to your personal copy.

## Configuration

By default, the tool will ask you to input configuration details (playlist links etc.) via terminal.

The tool can also be configured via a YAML file, though.
This enables additional features like `setminus_playlist_link`.
If you wish to do so, provide the path to your config YAML file at the end of the command to run the script.
