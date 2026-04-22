from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ALL_DATES,
    ATTR_FRAKSJON_ID,
    CONF_NAME,
    DOMAIN,
)
from .coordinator import FolloRenovasjonDataUpdateCoordinator
from .entity_helpers import get_fraction_date_strings, get_fraction_name, merged_entry_config


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FolloRenovasjonDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[FolloRenovasjonSensor] = [
        FolloRenovasjonSensor(coordinator, entry, item["FraksjonId"])
        for item in coordinator.data
    ]
    async_add_entities(entities)


class FolloRenovasjonSensor(
    CoordinatorEntity[FolloRenovasjonDataUpdateCoordinator],
    SensorEntity,
):
    _attr_device_class = SensorDeviceClass.DATE
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FolloRenovasjonDataUpdateCoordinator,
        entry: ConfigEntry,
        fraksjon_id: int,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._fraksjon_id = fraksjon_id
        self._attr_unique_id = f"{entry.entry_id}_fraksjon_{fraksjon_id}"
        self._attr_translation_key = "pickup_date"

    @property
    def name(self) -> str:
        return f"{self._entry.data[CONF_NAME]} {self._display_name}"

    @property
    def native_value(self):
        dates = self._dates
        if not dates:
            return None

        return datetime.fromisoformat(dates[0]).date()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            ATTR_FRAKSJON_ID: self._fraksjon_id,
            ATTR_ALL_DATES: self._dates,
            "fraction_name": self._display_name,
        }

    @property
    def available(self) -> bool:
        return super().available and self._matching_item is not None

    @property
    def _matching_item(self) -> dict[str, Any] | None:
        return next(
            (
                item
                for item in self.coordinator.data
                if item.get("FraksjonId") == self._fraksjon_id
            ),
            None,
        )

    @property
    def _dates(self) -> list[str]:
        item = self._matching_item
        if item is None:
            return []

        return get_fraction_date_strings(item)

    @property
    def _display_name(self) -> str:
        return get_fraction_name(merged_entry_config(self._entry), self._fraksjon_id)
