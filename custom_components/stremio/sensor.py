import string
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import Entity
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .const import BASE_URL, CONF_MEDIA, ICON

SCAN_INTERVAL = timedelta(minutes=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MEDIA): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the currency sensor"""

    media = config["media"]

    add_entities(
        [StremioSensor(hass, media, SCAN_INTERVAL)],
        True,
    )


class StremioSensor(Entity):
    def __init__(self, hass, media, interval):
        """Inizialize sensor"""
        self._state = STATE_UNKNOWN
        self._hass = hass
        self._interval = interval
        self._media = media
        self._medias = []

    @property
    def name(self):
        """Return the name sensor"""
        if self._media == "movie":
            return "Stremio movies"
        return f"Stremio {self._media}"

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def state(self):
        """Return the state of the sensor"""
        return len(self._medias)

    @property
    def extra_state_attributes(self):
        """Attributes."""
        return {"data": self._medias}

    def update(self):
        """Get the latest update fron the api"""
        retry_strategy = Retry(
            total=3,
            status_forcelist=[400, 401, 404, 500, 502, 503, 504],
            method_whitelist=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.Session()
        http.mount("https://", adapter)

        url = BASE_URL.format(
            self._media,
        )

        response = http.get(url)
        self._medias.append(
            {
                "title_default": "$title",
                "line1_default": "$genres",
                "line2_default": "$release",
                "line3_default": "$runtime",
                "line4_default": "$rating",
                "icon": "mdi:arrow-down-bold",
            }
        )

        for media in response.json().get("metas"):

            released = media.get("released").split("T")[0] if media.get("released") else media.get("released")

            self._medias.append(
                dict(
                    title=media["name"],
                    rating=media.get("imdbRating"),
                    genres=media.get("genres"),
                    poster=media.get("poster"),
                    fanart=media.get("background"),
                    runtime=released,
                    release=released,
                    airdate=released,
                )
            )
