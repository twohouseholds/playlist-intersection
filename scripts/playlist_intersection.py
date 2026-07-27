#!/usr/bin/env python3
"""Output playlist intersection.

The maximum input playlist size is 10_000.
"""

import argparse
import logging
import os
import re
from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Any, Self, cast

import yaml
from pydantic import BaseModel
from spotipy import Spotify, SpotifyOAuth

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "playlist-read-private playlist-read-collaborative"

_logger = logging.getLogger(__name__)


class CliArgs(BaseModel):
    """Command line arguments."""

    config_path: Path
    output_path: Path


class Config(BaseModel):
    """Config for this script."""

    playlist_ids: list[str]


@dataclass(frozen=True)
@total_ordering
class Track(BaseModel):
    """Track in a playlist."""

    name: str
    main_artist: str
    secondary_artists_lexicographically: tuple[str, ...]

    def __lt__(self, other: Self) -> bool:
        """Compare tracks by main artist, then by name."""
        if self.main_artist == other.main_artist:
            return self.name < other.name
        return self.main_artist < other.main_artist


def main() -> None:
    """Run script."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args()
    playlist_intersection = get_playlist_intersection(
        get_config(args.config_path).playlist_ids,
        get_spotify_client(),
    )
    write_output(playlist_intersection, args.output_path)


def parse_args() -> CliArgs:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        dest="config_path",
        type=Path,
        help="Path to the YAML config file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output_path",
        type=Path,
        default=Path(__file__).parent.parent / "output.txt",
        help="Path to the output text file.",
    )
    parsed_args = parser.parse_args()
    return CliArgs(
        config_path=parsed_args.config_path,
        output_path=parsed_args.output_path,
    )


def get_config(config_path: Path) -> Config:
    """Read, parse and validate config."""
    _logger.info("Reading config")
    raw_config = config_path.read_text()
    parsed_conifg = yaml.safe_load(raw_config)
    return Config.model_validate(parsed_conifg)


def get_spotify_client() -> Spotify:
    """Create spotify client from credentials in environment variables."""
    _logger.info("Creating Spotify client")
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


def get_playlist_intersection(
    playlist_ids: list[str],
    spotify_client: Spotify,
) -> list[Track]:
    """Get the intersection of the playlists from ``playlist_ids``."""
    _logger.info("Reading playlists")
    tracks_by_playlist: list[set[Track]] = []
    for index, playlist_id in enumerate(playlist_ids):
        _logger.info(
            "%.1f%% - %s",
            index / len(playlist_ids) * 100,
            get_metadata_str(playlist_id, spotify_client),
        )
        tracks_by_playlist.append(get_tracks(playlist_id, spotify_client))
    _logger.info("Computing intersection")
    playlist_intersection = set.intersection(*tracks_by_playlist)
    return sorted(playlist_intersection)


def get_tracks(
    playlist_id: str,
    spotify_client: Spotify,
) -> set[Track]:
    """Get the of tracks from ``playlist_id``.

    Spotify allows a limit up to 100 tracks per request. Therefore, 100 requests are
    sent for 100 tracks each, leading to the maximum input playlist size of 10_000.
    """
    tracks: set[Track] = set()
    for offset in range(0, 10_000, 100):
        raw_items = cast(
            "dict[str, Any]",
            spotify_client.playlist_tracks(playlist_id, offset=offset, limit=100),
        )
        items = cast("list[dict[str,Any]]", raw_items["items"])
        for item_dict in items:
            item = cast("dict[str, Any]", item_dict["item"])
            name = re.sub(r" \(feat\. .*\)", "", item["name"])
            artist_dicts = cast("list[dict[str, Any]]", item["artists"])
            main_artist = str(artist_dicts[0]["name"])
            secondary_artists = {
                str(artist_dict["name"]) for artist_dict in artist_dicts
            } - {main_artist}
            tracks.add(
                Track(
                    name=name,
                    main_artist=main_artist,
                    secondary_artists_lexicographically=tuple(
                        sorted(secondary_artists),
                    ),
                ),
            )
        if len(items) < 100:  # noqa: PLR2004
            break
    return tracks


def get_metadata_str(
    playlist_id: str,
    spotify_client: Spotify,
) -> str:
    """Log playlist metadata."""
    metadata = cast(
        "dict[str, Any]",
        spotify_client.playlist(playlist_id),
    )
    playlist_name = cast("str", metadata.get("name"))
    is_public = cast("bool", metadata.get("public"))
    owner_metadata = cast("dict[str, str]", metadata["owner"])
    owner_name = owner_metadata["display_name"]
    return f"'{playlist_name}' by '{owner_name}' ({
        'public' if is_public else 'non-public'
    })"


def write_output(playlist_intersection: list[Track], output_path: Path) -> None:
    """Write output."""
    _logger.info("Creating output")
    output = []
    for track in playlist_intersection:
        output_line = f"{track.main_artist} - {track.name}"
        features = track.secondary_artists_lexicographically
        if features:
            output_line += f" (feat. {', '.join(features)})"
        output.append(output_line)
    output_path.write_text("\n".join(output), encoding="utf-8")


if __name__ == "__main__":
    main()
