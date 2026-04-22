from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

homeassistant_module = types.ModuleType("homeassistant")
config_entries_module = types.ModuleType("homeassistant.config_entries")


class _DummyConfigEntry:
    def __init__(self, data: dict, options: dict) -> None:
        self.data = data
        self.options = options


config_entries_module.ConfigEntry = _DummyConfigEntry
homeassistant_module.config_entries = config_entries_module

sys.modules.setdefault("homeassistant", homeassistant_module)
sys.modules.setdefault("homeassistant.config_entries", config_entries_module)


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to create module spec for {module_name}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


root = Path(__file__).resolve().parents[1]
package_root = root / "custom_components" / "folloren"

custom_components_package = types.ModuleType("custom_components")
custom_components_package.__path__ = [str(root / "custom_components")]
sys.modules.setdefault("custom_components", custom_components_package)

folloren_package = types.ModuleType("custom_components.folloren")
folloren_package.__path__ = [str(package_root)]
sys.modules.setdefault("custom_components.folloren", folloren_package)

_load_module("custom_components.folloren.const", package_root / "const.py")
entity_helpers = _load_module(
    "custom_components.folloren.entity_helpers",
    package_root / "entity_helpers.py",
)

get_fraction_dates = entity_helpers.get_fraction_dates
get_fraction_name = entity_helpers.get_fraction_name
get_pickup_days = entity_helpers.get_pickup_days
get_pickup_events = entity_helpers.get_pickup_events
merged_entry_config = entity_helpers.merged_entry_config


def test_get_fraction_name_uses_mapping_when_present() -> None:
    config = {"fraksjon_names": '{"1": "Restavfall", "2": "Papir"}'}

    assert get_fraction_name(config, 1) == "Restavfall"
    assert get_fraction_name(config, 2) == "Papir"


def test_get_fraction_name_falls_back_on_invalid_mapping() -> None:
    config = {"fraksjon_names": "{invalid json"}

    assert get_fraction_name(config, 5) == "fraksjon 5"


def test_get_fraction_dates_deduplicates_and_sorts() -> None:
    item = {
        "Tommedatoer": [
            "2026-05-01T00:00:00",
            "2026-04-25T00:00:00",
            "2026-05-01T00:00:00",
            "not-a-date",
        ]
    }

    result = get_fraction_dates(item)

    assert [value.isoformat() for value in result] == ["2026-04-25", "2026-05-01"]


def test_get_pickup_events_deduplicates_by_fraction_and_date() -> None:
    config = {"fraksjon_names": '{"1": "Rest", "2": "Papir"}'}
    data = [
        {
            "FraksjonId": 1,
            "Tommedatoer": ["2026-05-01T00:00:00", "2026-05-01T00:00:00"],
        },
        {
            "FraksjonId": 1,
            "Tommedatoer": ["2026-05-03T00:00:00"],
        },
        {
            "FraksjonId": 2,
            "Tommedatoer": ["2026-05-01T00:00:00"],
        },
    ]

    result = get_pickup_events(config, data)

    assert [(event.fraksjon_id, event.pickup_date.isoformat()) for event in result] == [
        (1, "2026-05-01"),
        (2, "2026-05-01"),
        (1, "2026-05-03"),
    ]
    assert result[0].fraction_name == "Rest"
    assert result[1].fraction_name == "Papir"


def test_get_pickup_days_groups_multiple_fractions_same_day() -> None:
    config = {"fraksjon_names": '{"1": "Rest", "2": "Papir"}'}
    data = [
        {
            "FraksjonId": 2,
            "Tommedatoer": ["2026-05-01T00:00:00"],
        },
        {
            "FraksjonId": 1,
            "Tommedatoer": ["2026-05-01T00:00:00", "2026-05-02T00:00:00"],
        },
    ]

    result = get_pickup_days(config, data)

    assert len(result) == 2
    assert result[0].pickup_date.isoformat() == "2026-05-01"
    assert result[0].fraksjon_ids == (1, 2)
    assert result[0].fraction_names == ("Rest", "Papir")


def test_merged_entry_config_prefers_options() -> None:
    entry = _DummyConfigEntry(data={"a": 1, "b": 2}, options={"b": 3, "c": 4})

    result = merged_entry_config(entry)

    assert result == {"a": 1, "b": 3, "c": 4}