from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry

from .const import CONF_FRAKSJON_NAMES


@dataclass(frozen=True, slots=True)
class PickupEvent:
    fraksjon_id: int
    fraction_name: str
    pickup_date: date


@dataclass(frozen=True, slots=True)
class PickupDay:
    pickup_date: date
    fraksjon_ids: tuple[int, ...]
    fraction_names: tuple[str, ...]


def merged_entry_config(entry: ConfigEntry) -> dict[str, Any]:
    return {**entry.data, **entry.options}


def get_fraction_name(config: dict[str, Any], fraksjon_id: int) -> str:
    configured_names = config.get(CONF_FRAKSJON_NAMES, "")

    if isinstance(configured_names, str) and configured_names.strip():
        try:
            parsed = json.loads(configured_names)
        except json.JSONDecodeError:
            parsed = {}

        if isinstance(parsed, dict):
            configured_name = parsed.get(str(fraksjon_id))
            if isinstance(configured_name, str) and configured_name.strip():
                return configured_name.strip()

    return f"fraksjon {fraksjon_id}"


def get_fraction_date_strings(item: dict[str, Any]) -> list[str]:
    return [pickup_date.isoformat() for pickup_date in get_fraction_dates(item)]


def get_fraction_dates(item: dict[str, Any]) -> list[date]:
    raw_dates = item.get("Tommedatoer", [])
    if not isinstance(raw_dates, list):
        return []

    unique_dates: set[date] = set()
    dates: list[date] = []
    for raw_date in raw_dates:
        try:
            pickup_date = datetime.fromisoformat(str(raw_date)).date()
        except ValueError:
            continue

        if pickup_date in unique_dates:
            continue

        unique_dates.add(pickup_date)
        dates.append(pickup_date)

    dates.sort()
    return dates


def get_pickup_events(
    config: dict[str, Any],
    data: list[dict[str, Any]] | None,
) -> list[PickupEvent]:
    if not data:
        return []

    seen: set[tuple[int, date]] = set()
    pickup_events: list[PickupEvent] = []

    for item in data:
        fraksjon_id = item.get("FraksjonId")
        if not isinstance(fraksjon_id, int):
            continue

        fraction_name = get_fraction_name(config, fraksjon_id)
        for pickup_date in get_fraction_dates(item):
            dedupe_key = (fraksjon_id, pickup_date)
            if dedupe_key in seen:
                continue

            seen.add(dedupe_key)
            pickup_events.append(
                PickupEvent(
                    fraksjon_id=fraksjon_id,
                    fraction_name=fraction_name,
                    pickup_date=pickup_date,
                )
            )

    pickup_events.sort(key=lambda item: (item.pickup_date, item.fraksjon_id))
    return pickup_events


def get_pickup_days(
    config: dict[str, Any],
    data: list[dict[str, Any]] | None,
) -> list[PickupDay]:
    grouped_by_date: dict[date, dict[int, str]] = {}

    for pickup_event in get_pickup_events(config, data):
        grouped_by_date.setdefault(pickup_event.pickup_date, {})[
            pickup_event.fraksjon_id
        ] = pickup_event.fraction_name

    pickup_days = [
        PickupDay(
            pickup_date=pickup_date,
            fraksjon_ids=tuple(sorted(fraksjoner)),
            fraction_names=tuple(
                fraksjoner[fraksjon_id] for fraksjon_id in sorted(fraksjoner)
            ),
        )
        for pickup_date, fraksjoner in grouped_by_date.items()
    ]
    pickup_days.sort(key=lambda item: item.pickup_date)
    return pickup_days
