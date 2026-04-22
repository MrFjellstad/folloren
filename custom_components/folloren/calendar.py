from __future__ import annotations

from datetime import date, datetime, time, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DOMAIN
from .coordinator import FolloRenovasjonDataUpdateCoordinator
from .entity_helpers import PickupDay, get_pickup_days, merged_entry_config


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FolloRenovasjonDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FolloRenovasjonCalendar(coordinator, entry)])


class FolloRenovasjonCalendar(
    CoordinatorEntity[FolloRenovasjonDataUpdateCoordinator],
    CalendarEntity,
):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: FolloRenovasjonDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def name(self) -> str:
        return f"{self._entry.data[CONF_NAME]} kalender"

    @property
    def event(self) -> CalendarEvent | None:
        today = date.today()
        for pickup_day in self._pickup_days:
            if pickup_day.pickup_date >= today:
                return _as_calendar_event(pickup_day)
        return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        return [
            _as_calendar_event(pickup_day)
            for pickup_day in self._pickup_days
            if _event_overlaps_range(pickup_day, start_date, end_date)
        ]

    @property
    def _pickup_days(self) -> list[PickupDay]:
        return get_pickup_days(
            merged_entry_config(self._entry),
            self.coordinator.data,
        )


def _as_calendar_event(pickup_day: PickupDay) -> CalendarEvent:
    fraction_names = ", ".join(pickup_day.fraction_names)
    fraksjon_ids = ", ".join(str(fraksjon_id)
                             for fraksjon_id in pickup_day.fraksjon_ids)

    return CalendarEvent(
        summary=f"Tømming: {fraction_names}",
        start=pickup_day.pickup_date,
        end=pickup_day.pickup_date + timedelta(days=1),
        description=(
            f"Fraksjon {fraksjon_ids}: {fraction_names}"
        ),
    )


def _event_overlaps_range(
    pickup_day: PickupDay,
    start_date: datetime,
    end_date: datetime,
) -> bool:
    tzinfo = start_date.tzinfo
    event_start = datetime.combine(
        pickup_day.pickup_date, time.min, tzinfo=tzinfo)
    event_end = event_start + timedelta(days=1)
    return event_start < end_date and event_end > start_date
