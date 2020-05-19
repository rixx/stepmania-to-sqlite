import hashlib
import json
import subprocess
from pathlib import Path

import click
from tqdm import tqdm

DEBUG = True


class SongException(Exception):
    pass


def error(message):
    click.secho("ERROR: " + message, bold=True, fg="red")


def warning(message):
    click.secho("WARNING: " + message, bold=True)


class Song:
    def __init__(self, path):
        self.path = path
        self.id = get_song_id(self.path)
        self.song_path = self.get_song_path()
        self.metadata, self.charts = self.parse_file()
        self.title = self.metadata.get("title")
        self.artist = self.metadata.get("artist")
        if not (self.title and self.artist):
            raise SongException(
                f"Title or artist missing: {self.path}. Metadata: {self.metadata}"
            )
        self.bpms = self.parse_bpms()
        if not self.bpms:
            raise SongException(f"No BPM found: {self.path}")
        self.bpm = self.bpms[0] if len(self.bpms) == 1 else None
        self.seconds = self.get_duration()

    @property
    def data(self):
        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "group": self.path.parent.name,
            "bpm": self.bpm,
            "bpms": json.dumps(self.bpms),
            "seconds": self.seconds,
            "song_path": str(self.song_path),
            "metadata": json.dumps(self.metadata),
        }

    def get_song_path(self):
        files = list(self.path.parent.glob("*.ogg"))
        if not files:
            files = list(self.path.parent.glob("*.mp3"))
        if not files:
            raise SongException(
                f"No song file found for glob {self.path.parent / '*.ogg|mp3'}"
            )
        return files[0]

    def parse_metadata(self, lines):
        metadata = {}
        for line in lines:
            if line.startswith("#"):
                try:
                    key, value = line.strip().strip("#;").split(":", maxsplit=1)
                except Exception:
                    if DEBUG:
                        print(f"Skipping metadata line: {line}")
                    continue
                if key.strip():
                    metadata[key.strip().lower()] = value.strip()
        return metadata

    def parse_file(self):
        metadata_lines = []
        charts = []
        header = True
        current_chart = {
            "song_id": self.id,
            "steps": 0,
            "jumps": 0,
            "beats": 4,
        }
        chart_data = 0
        valid_chars = ["0", "1", "2", "3", "4", "M"]
        step_chars = ["1", "2"]

        # utf-8-sig strips BOMs
        with open(self.path, mode="r", encoding="utf-8-sig") as fp:
            for line in fp.readlines():
                line = line.strip()
                if not line:
                    continue

                if line.startswith("#NOTES"):
                    header = False
                    if "type" in current_chart:
                        raise SongException("New chart started before old one ended")
                    chart_data = 0

                elif header:
                    metadata_lines.append(line)

                elif chart_data is not None:
                    chart_data += 1
                    if chart_data == 1:
                        current_chart["type"] = line
                    elif chart_data == 3:
                        current_chart["difficulty"] = line.strip(":").lower()
                    elif chart_data == 4:
                        current_chart["meter"] = int(line.strip(":"))
                    elif chart_data == 5:
                        chart_data = None
                else:
                    if len(line) >= 4 and all(char in valid_chars for char in line[:4]):
                        data = line[:4]
                        step_count = sum(
                            (character in step_chars for character in data), 0
                        )
                        if step_count:
                            current_chart["steps"] += 1
                        if step_count > 1:
                            current_chart["jumps"] += 1
                    elif line.startswith(","):
                        current_chart["beats"] += 4
                    elif line.startswith(";"):
                        current_chart["id"] = (
                            self.id
                            + f"-{current_chart['difficulty']}-{current_chart['meter']}"
                        )
                        charts.append(current_chart)
                        current_chart = {
                            "song_id": self.id,
                            "steps": 0,
                            "jumps": 0,
                            "beats": 4,
                        }

        return self.parse_metadata(metadata_lines), charts

    def parse_bpms(self):
        return [
            int(float(value.split("=")[-1]))
            for value in self.metadata["bpms"].split(",")
        ]

    def get_duration(self):
        data = subprocess.check_output(
            ["ffprobe", self.song_path], stderr=subprocess.STDOUT
        ).decode()
        duration_line = [
            line.strip()
            for line in data.split("\n")
            if line.strip().startswith("Duration")
        ][0]
        durations = duration_line[len("Duration: ") :].split(", ")[0].split(":")
        return int(float(durations[-1])) + 60 * int(durations[-2])


def save_charts(db, charts):
    charts_table = db.table("charts", pk="id")
    charts_table.insert_all(
        charts, replace=True, alter=True, foreign_keys=(("song_id", "songs", "id"),)
    )


def save_songs(db, songs):
    charts = [chart for song in songs for chart in song.charts]
    songs_table = db.table("songs", pk="id")
    songs_table.insert_all(
        [song.data for song in songs], pk="id", replace=True, alter=True
    )
    save_charts(db, charts)


def get_song_id(path):
    return hashlib.md5(str(path).encode()).hexdigest()


def get_songs(db, changed_only=True, save=True, location=None):
    known_songs = {song["id"]: True for song in db["songs"].rows}

    songs = []
    for path in tqdm(list(Path.home().glob(".stepmania*/Songs/**/**/*.sm"))):
        song_id = get_song_id(path)
        is_known = known_songs.pop(song_id, None)
        if changed_only and is_known:
            continue
        try:
            songs.append(Song(path))
        except UnicodeDecodeError:
            continue
        except SongException as e:
            if DEBUG:
                warning(str(e))
            continue
        except Exception as e:
            if DEBUG:
                error(str(e))
                raise
            continue
    db["songs"].delete_where("id in ?", known_songs.keys())
    if save:
        save_songs(db, songs)
    return songs
