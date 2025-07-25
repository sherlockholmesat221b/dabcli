import os
from api import get
from config import config
from utils import require_login
from downloader import download_track
from converter import convert_audio
from tagger import tag_audio
from cover import download_cover_image

def sanitize_filename(name):
    return ''.join(c for c in name if c.isalnum() or c in ' _-').rstrip()

def download_library(library_id: str, quality: str = None):
    if not require_login(config):
        return

    result = get(f"/libraries/{library_id}")
    if not result or "library" not in result:
        print("[Library] Failed to load library.")
        return

    library = result["library"]
    tracks = library.get("tracks", [])
    if not tracks:
        print("[Library] No tracks found.")
        return

    title = sanitize_filename(library.get("title", f"library_{library_id}"))
    output_format = config.output_format
    quality = quality or ("27" if output_format == "flac" else "5")

    lib_folder = os.path.join(config.output_directory, f"{title} [{output_format.upper()}]")
    os.makedirs(lib_folder, exist_ok=True)

    print(f"[Library] Downloading: {title} ({len(tracks)} tracks)")

    playlist_paths = []
    for idx, track in enumerate(tracks, 1):
        print(f"[{idx}/{len(tracks)}] {track['title']} — {track['artist']}")

        raw_path = download_track(
            track_id=track["id"],
            quality=quality,
            directory=lib_folder,
            track_meta=track
        )
        if not raw_path:
            print("[Library] Skipping: download failed.")
            continue

        converted_path = convert_audio(raw_path, output_format)
        if not converted_path:
            print("[Library] Skipping: conversion failed.")
            continue

        metadata = {
            "title": track.get("title", ""),
            "artist": track.get("artist", ""),
            "album": track.get("albumTitle", ""),
            "genre": track.get("genre", ""),
            "date": track.get("releaseDate", "")[:4]
        }

        cover_url = track.get("albumCover")
        cover_path = None
        if cover_url:
            cover_path = download_cover_image(
                cover_url, os.path.join(lib_folder, f"cover_{track['id']}.jpg")
            )

        tag_audio(converted_path, metadata, cover_path=cover_path)

        if cover_path and os.path.exists(cover_path) and not config.keep_cover_file:
            try:
                os.remove(cover_path)
            except Exception:
                pass

        if config.delete_raw_files and raw_path != converted_path:
            try:
                os.remove(raw_path)
            except Exception as e:
                print(f"[Library] Could not delete raw file: {e}")

        playlist_paths.append(os.path.basename(converted_path))

    m3u_path = os.path.join(lib_folder, "library.m3u8")
    with open(m3u_path, "w", encoding="utf-8") as m3u:
        for filename in playlist_paths:
            m3u.write(filename + "\n")

    print(f"[Library] Finished: {len(playlist_paths)} tracks saved to {lib_folder}")
    print(f"[Library] Playlist written to: {m3u_path}")