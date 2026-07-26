# Playlist Intersection

Display the intersection (common songs) of two playlists (as Spotify currently does not support this).

## Setup

1. Clone the repository.
2. Rename `.env.template` to `.env`.
3. Spotify Web API credentials:
   1. Log in to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   2. Create an app with the `Redirect URIs` set to `http://127.0.0.1:8888/callback` and `Which API/SDKs are you planning to use?` set to `Web API`.
   3. Copy the `Client ID` and `Client Secret` to the respective environment variables in `.env`.
4. Spotify playlist IDs:
   1. Get the IDs of the playlists you want the intersection of. The ID can be found in the playlists link, e.g., if the link is `https://open.spotify.com/playlist/abc123`, the ID is `abc123`.
   2. Enter the playlist IDs to the respective environment variable in `.env`, seperated by `;`.
5. Install `uv` and run `uv sync --all-packages`.
6. Run the script: `uv run --env-file .env python main.py`.
