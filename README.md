# Playlist Intersection

Tool to create an intersection playlist with the common tracks of a number of playlists (as Spotify currently does not support this).

## Setup

1. Clone the repository.
2. Install `uv` and run `uv sync --all-packages` (in the directory of your clone).
3. Rename `.env.template` to `.env` and enter your Spotify Web API credentials:
   1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   2. Create an app with the `Redirect URIs` set to `http://127.0.0.1:8888/callback` and `Which API/SDKs are you planning to use?` set to `Web API`.
   3. Copy the `Client ID` and `Client Secret` to the respective environment variables in `.env`.
4. In `data/`, rename `config.template.yaml` to `config.yaml` and configure the tool:
   1. Enter the `output_playlist_name`.
   2. Enter the `playlist_ids` of the playlists you want the intersection of.
      - The playlist ID can be found in the playlist's link. E.g., if the link is `https://open.spotify.com/playlist/abc123`, the ID is `abc123`.
5. Run the script: `uv run --env-file .env python scripts/playlist_intersection.py data/config.yaml`.
   - If the script fails with `403 Forbidden` for a playlist that you can access via Spotify UI, try using a personal copy: Go to the playlist -> three dots -> `Add to other playlist` -> `New playlist`. Now use the ID of your personal copy.
