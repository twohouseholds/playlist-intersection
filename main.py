"""Output playlist intersection."""

import logging
import os
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel
from spotipy import Spotify, SpotifyOAuth

OUTPUT_PATH = Path(__file__.replace(".py", ".txt"))

REDIRECT_URI = "http://127.0.0.1:8888/callback"

_logger = logging.getLogger(__name__)


def main() -> None:
    """Run script."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    _logger.info("Creating Spotify client")
    spotify_client = Spotify(
        auth_manager=SpotifyOAuth(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            redirect_uri=REDIRECT_URI,
            scope="playlist-read-private",
        ),
    )

    _logger.info("Reading playlist IDs")
    if not (raw_playlist_ids := os.getenv("SPOTIFY_PLAYLIST_IDS")):
        msg = "Environment variable 'SPOTIFY_PLAYLIST_IDS' is not set."
        raise ValueError(msg)
    playlist_ids: list[str] = raw_playlist_ids.split(";")

    playlist_intersection = get_playlist_intersection(playlist_ids, spotify_client)

    _logger.info("Creating output")
    OUTPUT_PATH.write_text("\n".join([f"{track}" for track in playlist_intersection]))


class Track(BaseModel):
    """Track in a playlist."""

    name: str
    main_artist: str
    artists_lexicographically: list[str]


def get_playlist_intersection(
    playlist_ids: list[str],
    spotify_client: Spotify,
) -> list[Track]:
    """Get the intersection of the playlists from ``playlist_ids``."""
    _logger.info("Reading playlists")
    tracks_by_playlist: list[set[Track]] = []
    for index, playlist_id in enumerate(playlist_ids, start=1):
        log_playlist_metadata(
            spotify_client,
            playlist_id,
            index_playlist=index,
            n_playlists=len(playlist_ids),
        )
        raw_items = cast(
            "dict[str, Any]",
            spotify_client.playlist_tracks(playlist_id, limit=1_000_000),
        )
        items = cast("list[dict[str,Any]]", raw_items["items"])
        tracks: set[Track] = set()
        for item_dict in items:
            item = cast("dict[str, Any]", item_dict["item"])
            name = item["name"]
            artist_dicts = cast("list[dict[str, Any]]", item["artists"])
            main_artist = str(artist_dicts[0]["name"])
            artists = [str(artist_dict["name"]) for artist_dict in artist_dicts]
            tracks.add(
                Track(
                    name=name,
                    main_artist=main_artist,
                    artists_lexicographically=sorted(artists),
                ),
            )
        tracks_by_playlist.append(tracks)
    _logger.info("Computing intersection")
    playlist_intersection = set.intersection(*tracks_by_playlist)
    return list(playlist_intersection)


def log_playlist_metadata(
    spotify_client: Spotify,
    playlist_id: str,
    *,
    index_playlist: int,
    n_playlists: int,
) -> None:
    """Log playlist metadata."""
    metadata = cast(
        "dict[str, Any]",
        spotify_client.playlist(playlist_id),
    )
    playlist_name = cast("str", metadata.get("name"))
    is_public = cast("bool", metadata.get("public"))
    owner_metadata = cast("dict[str, str]", metadata["owner"])
    owner_name = owner_metadata["display_name"]
    _logger.info(
        "Reading playlist %d/%d: '%s' by '%s' (%s)",
        index_playlist,
        n_playlists,
        playlist_name,
        owner_name,
        "public" if is_public else "non-public",
    )


if __name__ == "__main__":
    main()
