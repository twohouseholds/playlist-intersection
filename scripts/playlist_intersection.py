#!/usr/bin/env python3
"""Create an intersection playlist from the playlist IDs in the given config file."""

import argparse
import logging
import os
import re
from argparse import Namespace
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Any, cast, override

import yaml
from pydantic import BaseModel
from spotipy import Spotify, SpotifyOAuth

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "playlist-read-private playlist-read-collaborative playlist-modify-public"

_logger = logging.getLogger(__name__)


class Config(BaseModel):
    """Config for this script."""

    output_playlist_name: str
    playlist_ids: list[str]
    setminus_playlist_id: str | None = None


def main() -> None:
    """Run script."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    config = Config.model_validate(yaml.safe_load(parse_args().config_path.read_text()))
    spotify_client = get_spotify_client()
    intersection_track_uris = get_intersection_track_uris(
        config.playlist_ids,
        config.setminus_playlist_id,
        spotify_client,
    )
    create_playlist(
        config.output_playlist_name,
        intersection_track_uris,
        spotify_client,
    )


def parse_args() -> Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        dest="config_path",
        type=Path,
        help="Path to the YAML config file.",
    )
    return parser.parse_args()


def get_spotify_client() -> Spotify:
    """Create spotify client from credentials in environment variables."""
    if not (client_id := os.getenv("SPOTIFY_CLIENT_ID")):
        msg = "Environment variable 'SPOTIFY_CLIENT_ID' is not set."
        raise ValueError(msg)
    if not (client_secret := os.getenv("SPOTIFY_CLIENT_SECRET")):
        msg = "Environment variable 'SPOTIFY_CLIENT_SECRET' is not set."
        raise ValueError(msg)
    return Spotify(
        auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
        ),
    )


@dataclass(frozen=True)
@total_ordering
class Track:
    """Track in a playlist."""

    uri: str
    name: str
    main_artist: str

    @override
    def __eq__(self, other: object) -> bool:
        """Compare tracks by main artist and name only."""
        if not isinstance(other, Track):
            return NotImplemented
        return self.main_artist == other.main_artist and self.name == other.name

    @override
    def __hash__(self) -> int:
        """Hash tracks by main artist and name only."""
        return hash((self.main_artist, self.name))

    def __lt__(self, other: object) -> bool:
        """Compare tracks by main artist, then by name."""
        if not isinstance(other, Track):
            return NotImplemented
        if self.main_artist == other.main_artist:
            return self.name.lower() < other.name.lower()
        return self.main_artist.lower() < other.main_artist.lower()


def get_intersection_track_uris(
    playlist_ids: list[str],
    setminus_playlist_id: str | None,
    spotify_client: Spotify,
) -> list[str]:
    """Get the intersection of the playlists from ``playlist_ids``."""
    if not playlist_ids:
        return []
    _logger.info("Reading playlists")
    tracks_by_playlist = [
        get_tracks(playlist_id, spotify_client) for playlist_id in playlist_ids
    ]
    _logger.info("Computing intersection")
    intersection_tracks = set.intersection(*tracks_by_playlist)
    if setminus_playlist_id:
        intersection_tracks -= get_tracks(setminus_playlist_id, spotify_client)
    return [track.uri for track in sorted(intersection_tracks)]


def get_tracks(
    playlist_id: str,
    spotify_client: Spotify,
) -> set[Track]:
    """Get the tracks from ``playlist_id``.

    Spotify allows a limit up to 100 tracks per request. Therefore, requests for 100
    tracks each are sent until a response contains <100 tracks.
    """
    tracks: set[Track] = set()
    offset = 0
    limit = 100
    has_next_page = True
    while has_next_page:
        raw_items = cast(
            "dict[str, Any]",
            spotify_client.playlist_tracks(playlist_id, offset=offset, limit=limit),
        )
        items = cast("list[dict[str,Any]]", raw_items["items"])
        for item_dict in items:
            item = cast("dict[str, Any]", item_dict["item"])
            uri = str(item["uri"])
            name = re.sub(r" \(feat\. .*\)", "", item["name"])
            artist_dicts = cast("list[dict[str, Any]]", item["artists"])
            main_artist = str(artist_dicts[0]["name"])
            tracks.add(
                Track(
                    uri=uri,
                    name=name,
                    main_artist=main_artist,
                ),
            )
        has_next_page = len(items) == limit
        offset += limit
    return tracks


def create_playlist(
    name: str,
    track_uris: list[str],
    spotify_client: Spotify,
) -> None:
    """Create playlist."""
    _logger.info("Creating playlist '%s'", name)
    response_dict = cast(
        "dict[str, Any]",
        spotify_client.current_user_playlist_create(name),
    )
    playlist_id = str(response_dict["id"])
    for offset in range(0, len(track_uris), 100):
        spotify_client.playlist_add_items(
            playlist_id,
            track_uris[offset : offset + 100],
        )


if __name__ == "__main__":
    main()
