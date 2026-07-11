#!/usr/bin/env python3
"""Build a compact cinema knowledge graph from IMDb's official TSV datasets.

The resulting JSON contains a deliberately bounded set of notable feature films,
their directors, and up to five principal cast members. Selection is deterministic
and balances each release year with globally popular titles.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
import os
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

BASE_URL = "https://datasets.imdbws.com"
FILES = (
    "title.basics.tsv.gz",
    "title.ratings.tsv.gz",
    "title.crew.tsv.gz",
    "title.principals.tsv.gz",
    "name.basics.tsv.gz",
)
START_YEAR = 1970
END_YEAR = 2026
TARGET_FILMS = 360
PER_YEAR = 5
MIN_VOTES = 12_000
MAX_CAST = 5

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "imdb"
OUTPUT = ROOT / "public" / "data" / "cinema.json"


def download(filename: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    destination = CACHE / filename
    if destination.exists() and destination.stat().st_size > 0:
        print(f"Using cached {filename}")
        return destination
    url = f"{BASE_URL}/{filename}"
    print(f"Downloading {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "CinemaGraphDataBuilder/1.0"})
    with urllib.request.urlopen(request, timeout=180) as response, destination.open("wb") as target:
        while chunk := response.read(1024 * 1024):
            target.write(chunk)
    return destination


def rows(path: Path) -> Iterable[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def parse_int(value: str | None) -> int | None:
    if not value or value == "\\N":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def notoriety(rating: float, votes: int) -> float:
    # Vote count dominates, while rating gently separates similarly popular films.
    return math.log10(max(votes, 1)) * 2.8 + rating


def load_ratings(path: Path) -> dict[str, tuple[float, int]]:
    result: dict[str, tuple[float, int]] = {}
    for row in rows(path):
        votes = int(row["numVotes"])
        if votes >= MIN_VOTES:
            result[row["tconst"]] = (float(row["averageRating"]), votes)
    print(f"Ratings above threshold: {len(result):,}")
    return result


def choose_titles(path: Path, ratings: dict[str, tuple[float, int]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in rows(path):
        if row["titleType"] != "movie" or row["isAdult"] != "0":
            continue
        year = parse_int(row["startYear"])
        if year is None or year < START_YEAR or year > END_YEAR:
            continue
        rating_data = ratings.get(row["tconst"])
        if not rating_data:
            continue
        rating, votes = rating_data
        runtime = parse_int(row["runtimeMinutes"])
        genres = [] if row["genres"] == "\\N" else row["genres"].split(",")
        candidates.append(
            {
                "id": row["tconst"],
                "title": row["primaryTitle"],
                "originalTitle": row["originalTitle"],
                "year": year,
                "runtime": runtime,
                "genres": genres,
                "rating": rating,
                "votes": votes,
                "score": notoriety(rating, votes),
            }
        )

    by_year: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for film in candidates:
        by_year[film["year"]].append(film)
    for films in by_year.values():
        films.sort(key=lambda item: (item["score"], item["votes"], item["rating"]), reverse=True)

    selected: dict[str, dict[str, Any]] = {}
    for year in range(START_YEAR, END_YEAR + 1):
        for film in by_year.get(year, [])[:PER_YEAR]:
            selected[film["id"]] = film

    for film in sorted(candidates, key=lambda item: (item["score"], item["votes"]), reverse=True):
        if len(selected) >= TARGET_FILMS:
            break
        selected.setdefault(film["id"], film)

    films = sorted(selected.values(), key=lambda item: (item["year"], -item["votes"], item["title"]))
    print(f"Selected films: {len(films)} from {films[0]['year']} to {films[-1]['year']}")
    return films


def load_director_ids(path: Path, title_ids: set[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for row in rows(path):
        tconst = row["tconst"]
        if tconst not in title_ids:
            continue
        result[tconst] = [] if row["directors"] == "\\N" else row["directors"].split(",")
    return result


def load_cast(path: Path, title_ids: set[str]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows(path):
        tconst = row["tconst"]
        if tconst not in title_ids or row["category"] not in {"actor", "actress"}:
            continue
        if len(result[tconst]) >= MAX_CAST:
            continue
        characters: list[str] = []
        raw_characters = row.get("characters")
        if raw_characters and raw_characters != "\\N":
            try:
                parsed = json.loads(raw_characters)
                if isinstance(parsed, list):
                    characters = [str(value) for value in parsed[:3]]
            except json.JSONDecodeError:
                pass
        result[tconst].append(
            {
                "id": row["nconst"],
                "order": int(row["ordering"]),
                "characters": characters,
            }
        )
    for cast in result.values():
        cast.sort(key=lambda item: item["order"])
    return result


def load_names(path: Path, needed_ids: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows(path):
        nconst = row["nconst"]
        if nconst not in needed_ids:
            continue
        result[nconst] = {
            "id": nconst,
            "name": row["primaryName"],
            "birthYear": parse_int(row["birthYear"]),
            "deathYear": parse_int(row["deathYear"]),
            "professions": [] if row["primaryProfession"] == "\\N" else row["primaryProfession"].split(","),
        }
        if len(result) == len(needed_ids):
            break
    missing = needed_ids - result.keys()
    if missing:
        print(f"Warning: {len(missing)} names missing", file=sys.stderr)
    return result


def build() -> None:
    paths = {filename: download(filename) for filename in FILES}
    ratings = load_ratings(paths["title.ratings.tsv.gz"])
    films = choose_titles(paths["title.basics.tsv.gz"], ratings)
    title_ids = {film["id"] for film in films}

    director_ids = load_director_ids(paths["title.crew.tsv.gz"], title_ids)
    cast = load_cast(paths["title.principals.tsv.gz"], title_ids)
    needed_names = {
        nconst
        for title_id in title_ids
        for nconst in director_ids.get(title_id, [])
    }
    needed_names.update(
        member["id"]
        for title_id in title_ids
        for member in cast.get(title_id, [])
    )
    names = load_names(paths["name.basics.tsv.gz"], needed_names)

    clean_films: list[dict[str, Any]] = []
    people_roles: dict[str, set[str]] = defaultdict(set)
    people_film_counts: dict[str, int] = defaultdict(int)

    for film in films:
        directors = []
        for person_id in director_ids.get(film["id"], []):
            person = names.get(person_id)
            if not person:
                continue
            directors.append({"id": person_id, "name": person["name"]})
            people_roles[person_id].add("director")
            people_film_counts[person_id] += 1

        principal_cast = []
        for member in cast.get(film["id"], []):
            person = names.get(member["id"])
            if not person:
                continue
            principal_cast.append(
                {
                    "id": member["id"],
                    "name": person["name"],
                    "characters": member["characters"],
                }
            )
            people_roles[member["id"]].add("actor")
            people_film_counts[member["id"]] += 1

        clean_films.append(
            {
                "id": film["id"],
                "title": film["title"],
                "originalTitle": film["originalTitle"],
                "year": film["year"],
                "runtime": film["runtime"],
                "genres": film["genres"],
                "rating": film["rating"],
                "votes": film["votes"],
                "directors": directors,
                "cast": principal_cast,
            }
        )

    people = []
    for person_id in sorted(needed_names, key=lambda value: names.get(value, {}).get("name", value)):
        person = names.get(person_id)
        if not person:
            continue
        people.append(
            {
                **person,
                "roles": sorted(people_roles[person_id]),
                "filmCount": people_film_counts[person_id],
            }
        )

    years = [film["year"] for film in clean_films]
    payload = {
        "meta": {
            "source": "IMDb Non-Commercial Datasets",
            "sourceUrl": "https://developer.imdb.com/non-commercial-datasets/",
            "license": "Personal and non-commercial use only; subject to IMDb terms and conditions.",
            "generatedAt": os.environ.get("BUILD_TIMESTAMP", "2026-07-11T00:00:00Z"),
            "selection": {
                "description": "Deterministic blend of five highly voted films per release year plus globally notable films, ranked by IMDb vote count and rating.",
                "minimumVotes": MIN_VOTES,
                "targetFilms": TARGET_FILMS,
                "principalCastPerFilm": MAX_CAST,
            },
            "filmCount": len(clean_films),
            "personCount": len(people),
            "yearRange": [min(years), max(years)],
        },
        "films": clean_films,
        "people": people,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1024:.1f} KiB)")


if __name__ == "__main__":
    build()
