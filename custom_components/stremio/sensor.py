import json
import logging
import string
from collections import defaultdict
from datetime import datetime, timedelta

import homeassistant.helpers.config_validation as cv
import pytz
import requests
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_NAME,
    CONF_RESOURCES,
    STATE_UNKNOWN,
)
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

ICON = "mdi:television-classic"

SCAN_INTERVAL = timedelta(minutes=60)

ATTRIBUTION = "Data provided by stremio api"

DOMAIN = "stremio"

CONF_MEDIA = "media"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_MEDIA): cv.string,
    }
)

BASE_URL = "https://v3-cinemeta.strem.io/catalog/{}/top.json"


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
            return f"Stremio movies"
        return f"Stremio {self._media}"

    @property
    def icon(self):
        """Return the default icon"""
        return ICON

    @property
    def state(self):
        """Return the state of the sensor"""
        now = datetime.now()
        return now.strftime("%d-%m-%Y %H:%M:%S")

    @property
    def device_state_attributes(self):
        """Attributes."""
        return {"data": self._medias}

    def update(self):
        """Get the latest update fron the api"""
        url = BASE_URL.format(
            self._media,
        )

        response = requests.get(url)
        if response.ok:
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
                self._medias.append(
                    dict(
                        title=media["name"],
                        rating=media.get("imdbRating"),
                        genres=media.get("genres"),
                        poster=media.get("poster"),
                        fanart=media.get("background"),
                        runtime=media.get("released").split("T")[0] if media.get("released") else media.get("released"),
                        release=media.get("released").split("T")[0] if media.get("released") else media.get("released"),
                        airdate=media.get("released").split("T")[0] if media.get("released") else media.get("released"),
                    )
                )
        else:
            _LOGGER.error("Cannot perform the request")
