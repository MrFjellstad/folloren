from __future__ import annotations

DOMAIN = "folloren"

CONF_API_PROXY_URL = "api_proxy_url"
CONF_API_SERVER_URL = "api_server_url"
CONF_ENABLE_CALENDAR = "enable_calendar"
CONF_FRAKSJON_NAMES = "fraksjon_names"
CONF_GATEKODE = "gatekode"
CONF_GATENAVN = "gatenavn"
CONF_HEADER_APP_KEY = "header_app_key"
CONF_HEADER_KOMMUNENR = "header_kommunenr"
CONF_HUSNR = "husnr"
CONF_KOMMUNENR = "kommunenr"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_USER_AGENT = "user_agent"

DEFAULT_NAME = "FolloRen"
DEFAULT_API_PROXY_URL = "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx"
DEFAULT_API_SERVER_URL = "https://komteksky.norkart.no/MinRenovasjon.Api/api/tommekalender/"
DEFAULT_ENABLE_CALENDAR = True
DEFAULT_FRAKSJON_NAMES = ""
DEFAULT_GATEKODE = ""
DEFAULT_GATENAVN = ""
DEFAULT_HEADER_APP_KEY = ""
DEFAULT_HEADER_KOMMUNENR = ""
DEFAULT_HUSNR = ""
DEFAULT_KOMMUNENR = ""
DEFAULT_SCAN_INTERVAL = 24
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:91.0) "
    "Gecko/20100101 Firefox/91.0"
)

ATTR_ALL_DATES = "all_dates"
ATTR_FRAKSJON_ID = "fraksjon_id"
