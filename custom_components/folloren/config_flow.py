from __future__ import annotations

import json
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_API_PROXY_URL,
    CONF_API_SERVER_URL,
    CONF_ENABLE_CALENDAR,
    CONF_FRAKSJON_NAMES,
    CONF_GATEKODE,
    CONF_GATENAVN,
    CONF_HEADER_APP_KEY,
    CONF_HEADER_KOMMUNENR,
    CONF_HUSNR,
    CONF_KOMMUNENR,
    CONF_SCAN_INTERVAL,
    CONF_USER_AGENT,
    DEFAULT_API_PROXY_URL,
    DEFAULT_API_SERVER_URL,
    DEFAULT_ENABLE_CALENDAR,
    DEFAULT_FRAKSJON_NAMES,
    DEFAULT_GATEKODE,
    DEFAULT_GATENAVN,
    DEFAULT_HEADER_APP_KEY,
    DEFAULT_HEADER_KOMMUNENR,
    DEFAULT_HUSNR,
    DEFAULT_KOMMUNENR,
    DEFAULT_NAME,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_USER_AGENT,
    DOMAIN,
)
from .coordinator import async_validate_api_config
from .exceptions import CannotConnect, InvalidApiResponse


def _parse_fraction_names(raw_value: Any) -> dict[str, str]:
    if raw_value in (None, ""):
        return {}

    if not isinstance(raw_value, str):
        raise InvalidFractionNames

    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError as err:
        raise InvalidFractionNames from err

    if not isinstance(parsed, dict):
        raise InvalidFractionNames

    normalized: dict[str, str] = {}
    for key, value in parsed.items():
        if not isinstance(value, str) or not value.strip():
            raise InvalidFractionNames
        normalized[str(key).strip()] = value.strip()

    return normalized


def _build_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    values = user_input or {}

    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=values.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_API_PROXY_URL,
                default=values.get(CONF_API_PROXY_URL, DEFAULT_API_PROXY_URL),
            ): selector.TextSelector(),
            vol.Required(
                CONF_API_SERVER_URL,
                default=values.get(CONF_API_SERVER_URL,
                                   DEFAULT_API_SERVER_URL),
            ): selector.TextSelector(),
            vol.Required(
                CONF_KOMMUNENR,
                default=values.get(CONF_KOMMUNENR, DEFAULT_KOMMUNENR),
            ): selector.TextSelector(),
            vol.Required(
                CONF_GATENAVN,
                default=values.get(CONF_GATENAVN, DEFAULT_GATENAVN),
            ): selector.TextSelector(),
            vol.Required(
                CONF_GATEKODE,
                default=values.get(CONF_GATEKODE, DEFAULT_GATEKODE),
            ): selector.TextSelector(),
            vol.Required(
                CONF_HUSNR,
                default=values.get(CONF_HUSNR, DEFAULT_HUSNR),
            ): selector.TextSelector(),
            vol.Required(
                CONF_HEADER_KOMMUNENR,
                default=values.get(CONF_HEADER_KOMMUNENR,
                                   DEFAULT_HEADER_KOMMUNENR),
            ): selector.TextSelector(),
            vol.Required(
                CONF_HEADER_APP_KEY,
                default=values.get(CONF_HEADER_APP_KEY,
                                   DEFAULT_HEADER_APP_KEY),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_FRAKSJON_NAMES,
                default=values.get(CONF_FRAKSJON_NAMES,
                                   DEFAULT_FRAKSJON_NAMES),
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
            vol.Optional(
                CONF_ENABLE_CALENDAR,
                default=values.get(CONF_ENABLE_CALENDAR,
                                   DEFAULT_ENABLE_CALENDAR),
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_USER_AGENT,
                default=values.get(CONF_USER_AGENT, DEFAULT_USER_AGENT),
            ): selector.TextSelector(),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=values.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=168,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
        }
    )


class FolloRenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                _parse_fraction_names(user_input.get(CONF_FRAKSJON_NAMES))
                info = await async_validate_api_config(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidApiResponse:
                errors["base"] = "invalid_api_response"
            except InvalidFractionNames:
                errors["base"] = "invalid_fraction_names"
            else:
                await self.async_set_unique_id(info["unique_id"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return FolloRenOptionsFlow(entry)


class FolloRenOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        combined = {**self.entry.data, **self.entry.options}

        if user_input is not None:
            try:
                _parse_fraction_names(user_input.get(CONF_FRAKSJON_NAMES))
                await async_validate_api_config(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidApiResponse:
                errors["base"] = "invalid_api_response"
            except InvalidFractionNames:
                errors["base"] = "invalid_fraction_names"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(combined),
            errors=errors,
        )


class InvalidFractionNames(Exception):
    pass
