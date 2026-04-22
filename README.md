# FolloRen

Home Assistant HACS-integrasjon for a hente tømmedatoer fra Norkart Min Renovasjon API via proxy.

## Konfigurasjon

Integrasjonen støtter GUI-oppsett via Home Assistant.

Felter som kan settes i GUI:

- Proxy-URL
- API-server-URL
- kommunenr i query
- gatenavn
- gatekode
- husnr
- kommunenr i header
- RenovasjonAppKey
- fraksjonsnavn som JSON-mapping, for eksempel `{"1":"Restavfall","2":"Papir"}`
- User-Agent
- oppdateringsintervall

## Sensorer

Det opprettes én sensor per `FraksjonId` i API-responsen. Sensorens state er neste tømmedato, og alle datoer legges i attributtet `all_dates`.

## Kalender

Integrasjonen oppretter også én kalenderentitet som vises i Home Assistants innebygde kalender. Der samles alle tømmedatoer på ett sted.

Kalenderhendelser dedupliseres per fraksjon og dato, slik at samme tømming ikke legges inn flere ganger hvis API-et returnerer duplikate datoer ved senere oppslag.

## Linting

Kjor lint lokalt med Ruff:

```bash
ruff check custom_components
```
