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


def get_data(media: str) -> list:
    """Get The request from the api"""
    medias = []
    url = BASE_URL.format(
        media,
    )

    response = requests.get(url)
    if response.ok:
        medias.append(
            {
                "title_default": "$title",
                "line1_default": "$genres",
                "line2_default": "$release",
                "line3_default": "$rating",
                "line4_default": "$cast",
                "icon": "mdi:arrow-down-bold",
            }
        )

        for media in response.json().get("metas"):
            medias.append(
                dict(
                    title=media["name"],
                    rating=media.get("imdbRating"),
                    genres=media.get("genres"),
                    cast=media.get("cast"),
                    poster=media.get("poster"),
                    fanart=media.get("background"),
                    runtime=media.get("released"),
                    release=media.get("released"),
                    airdate=media.get("released"),
                )
            )
    else:
        _LOGGER.error("Cannot perform the request")
    return medias


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
        self._name = "Series"
        self._medias = []

    @property
    def name(self):
        """Return the name sensor"""
        return self._name

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
        self._medias = get_data(self._media)
