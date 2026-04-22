from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_API_PROXY_URL,
    CONF_API_SERVER_URL,
    CONF_GATEKODE,
    CONF_GATENAVN,
    CONF_HEADER_APP_KEY,
    CONF_HEADER_KOMMUNENR,
    CONF_HUSNR,
    CONF_KOMMUNENR,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USER_AGENT,
    DOMAIN,
)
from .exceptions import CannotConnect, InvalidApiResponse

LOGGER = logging.getLogger(__name__)


def _merged_config(entry: ConfigEntry) -> dict[str, Any]:
    return {**entry.data, **entry.options}


def build_request_url(config: dict[str, Any]) -> str:
    query = urlencode(
        {
            "kommunenr": str(config[CONF_KOMMUNENR]).strip(),
            "gatenavn": str(config[CONF_GATENAVN]).strip(),
            "gatekode": str(config[CONF_GATEKODE]).strip(),
            "husnr": str(config[CONF_HUSNR]).strip(),
        }
    )
    server_url = str(config[CONF_API_SERVER_URL]).rstrip("/") + f"/?{query}"
    outer_query = urlencode({"server": server_url})
    return f"{str(config[CONF_API_PROXY_URL]).strip()}?{outer_query}"


def build_headers(config: dict[str, Any]) -> dict[str, str]:
    return {
        "content-type": "application/json",
        "Kommunenr": str(config[CONF_HEADER_KOMMUNENR]).strip(),
        "RenovasjonAppKey": str(config[CONF_HEADER_APP_KEY]).strip(),
        "User-Agent": str(config.get(CONF_USER_AGENT, DEFAULT_USER_AGENT)).strip(),
    }


async def async_fetch_calendar(hass: HomeAssistant, config: dict[str, Any]) -> list[dict[str, Any]]:
    session = async_get_clientsession(hass)
    url = build_request_url(config)
    headers = build_headers(config)

    try:
        async with session.get(url, headers=headers, timeout=30) as response:
            response.raise_for_status()
            payload = await response.json(content_type=None)
    except (ClientError, TimeoutError, ValueError) as err:
        raise CannotConnect from err

    if not isinstance(payload, list):
        raise InvalidApiResponse

    for item in payload:
        if not isinstance(item, dict) or "FraksjonId" not in item or "Tommedatoer" not in item:
            raise InvalidApiResponse

    return payload


async def async_validate_api_config(hass: HomeAssistant, config: dict[str, Any]) -> dict[str, str]:
    payload = await async_fetch_calendar(hass, config)
    unique_id = (
        f"{config[CONF_KOMMUNENR]}-"
        f"{str(config[CONF_GATENAVN]).strip().lower()}-"
        f"{config[CONF_GATEKODE]}-{config[CONF_HUSNR]}"
    )
    return {"title": str(config[CONF_NAME]), "unique_id": unique_id, "count": str(len(payload))}


class FolloRenovasjonDataUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        config = _merged_config(entry)
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=int(config.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))),
        )

    async def _async_update_data(self) -> list[dict[str, Any]]:
        try:
            return await async_fetch_calendar(self.hass, _merged_config(self.entry))
        except (CannotConnect, InvalidApiResponse) as err:
            raise UpdateFailed(str(err)) from err
