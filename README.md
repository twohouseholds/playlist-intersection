# Playlist Intersection

Output the intersection (common songs) of two playlists (as Spotify currently does not support this). The maximum input playlist size is 10_000.

## Example Output

```

```

## Setup

1. Clone the repository.
2. Rename `.env.template` to `.env`.
3. Enter your Spotify Web API credentials:
   1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   2. Create an app with the `Redirect URIs` set to `http://127.0.0.1:8888/callback` and `Which API/SDKs are you planning to use?` set to `Web API`.
   3. Copy the `Client ID` and `Client Secret` to the respective environment variables in `.env`.
4. Enter the Spotify playlist IDs of the playlists you want the intersection of in `config.yaml`. The playlist ID can be found in the playlist's link - e.g., if the link is `https://open.spotify.com/playlist/abc123`, the ID is `abc123`.
   - If the script fails with `403 Forbidden` for a playlist that you can access via Spotify, try using a personal copy: Go to the playlist -> three dots -> `Add to other playlist` -> `New playlist`. Now use the ID of your personal copy.
5. Install `uv` and run `uv sync --all-packages`.
6. Run the script: `uv run --env-file .env python main.py config.yaml`.
