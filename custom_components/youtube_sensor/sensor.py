"""
A platform which give you info about the newest video on a channel.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/youtube
"""

import logging
import async_timeout
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from dateutil.parser import parse
from homeassistant.const import CONF_NAME
import re
import html

CONF_CHANNEL_ID = 'channel_id'
ICON = 'mdi:youtube'
DOMAIN = 'youtube_sensor'

BASE_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id={}'
CHANNEL_LIVE_URL = 'https://www.youtube.com/channel/{}'
SHORTS_URL = 'https://www.youtube.com/shorts/{}'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CHANNEL_ID): cv.string,
    vol.Optional(CONF_NAME): cv.string,
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):  # pylint: disable=unused-argument
    """Setup sensor platform."""
    channel_id = config['channel_id']
    custom_name = config.get('name')  # Nome personalizzato opzionale
    session = async_create_clientsession(hass)
    
    try:
        url = BASE_URL.format(channel_id)
        async with async_timeout.timeout(10):
            response = await session.get(url)
            info = await response.text()
        name = info.split('<title>')[1].split('</')[0]
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.debug('Unable to set up - %s', error)
        name = None

    if name is not None:
        # Usa il nome personalizzato se fornito, altrimenti usa quello dal canale
        display_name = custom_name if custom_name else name
        async_add_entities([YoutubeSensor(channel_id, display_name, session)], True)

class YoutubeSensor(Entity):
    """YouTube Sensor class"""
    def __init__(self, channel_id, name, session):
        self._state = None
        self.session = session
        self._image = None
        self.stars = 0
        self.views = 0
        self.stream = False
        self.live = False
        self._name = name
        self.channel_id = channel_id
        self.url = None
        self.content_id = None
        self.published = None
        self.channel_live = False
        self.channel_image = None
        self.expiry = parse('01 Jan 1900 00:00:00 UTC')
        self.stream_start = None
        self.is_short = False

    async def async_update(self):
        """Update sensor."""
        _LOGGER.debug('%s - Running update', self._name)
        try:
            url = BASE_URL.format(self.channel_id)
            async with async_timeout.timeout(10):
                response = await self.session.get(url)
                info = await response.text()
            exp = parse(response.headers['Expires'])
            if exp < self.expiry:
                return
            self.expiry = exp
            title = info.split('<title>')[2].split('</')[0]
            url = info.split('<link rel="alternate" href="')[2].split('"/>')[0]
            if self.live or url != self.url:
                self.stream, self.live, self.stream_start = await is_live(url, self._name, self.hass, self.session)
            else:
                _LOGGER.debug('%s - Skipping live check', self._name)
            self.url = url
            self.content_id = url.split('?v=')[1]
            self.published = info.split('<published>')[2].split('</')[0]
            thumbnail_url = info.split(
                '<media:thumbnail url="')[1].split('"')[0]
            self._state = html.unescape(title)
            self._image = thumbnail_url
            self.stars = info.split('<media:starRating count="')[1].split('"')[0]
            self.views = info.split('<media:statistics views="')[1].split('"')[0]
            
            # Check if video is a YouTube Short - VERSIONE CORRETTA
            self.is_short = await is_youtube_short(self.content_id, self._name, self.session)
            
            url = CHANNEL_LIVE_URL.format(self.channel_id)
            self.channel_live, self.channel_image = await is_channel_live(url, self.name, self.hass, self.session)
        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.debug('%s - Could not update - %s', self._name, error)

    @property
    def name(self):
        """Name."""
        # Aggiungi il prefisso "youtube_" al nome per creare l'entity ID desiderato
        return f"youtube_{self._name}"

    @property
    def entity_picture(self):
        """Picture."""
        return self._image

    @property
    def state(self):
        """State."""
        return self._state

    @property
    def unique_id(self):
        """Return unique ID for this sensor."""
        # Usa il nome del sensore per creare un ID unico più leggibile
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', self._name.lower())
        return f"youtube_{safe_name}"

    @property
    def icon(self):
        """Icon."""
        return ICON

    @property
    def extra_state_attributes(self):
        """Attributes."""
        return {'url': self.url,
                'content_id': self.content_id,
                'published': self.published,
                'stars': self.stars,
                'views': self.views,
                'stream': self.stream,
                'stream_start': self.stream_start,
                'live': self.live,
                'channel_is_live': self.channel_live,
                'channel_image': self.channel_image,
                'is_short': self.is_short,
                'friendly_name': self._name}

async def is_live(url, name, hass, session):
    """Return bool if video is stream and bool if video is live"""
    live = False
    stream = False
    start = None
    try:
        async with async_timeout.timeout(10):
            response = await session.get(url, cookies=dict(CONSENT="YES+cb"))
            info = await response.text()
        if 'isLiveBroadcast' in info:
            stream = True
            start = parse(info.split('startDate" content="')[1].split('"')[0])
            if 'endDate' not in info:
                live = True
                _LOGGER.debug('%s - Latest Video is live', name)
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.debug('%s - Could not update - %s', name, error)
    return stream, live, start

async def is_channel_live(url, name, hass, session):
    """Return bool if channel is live"""
    live = False
    try:
        async with async_timeout.timeout(10):
            response = await session.get(url, cookies=dict(CONSENT="YES+cb"))
            info = await response.text()
        if '{"iconType":"LIVE"}' in info:
            live = True
            _LOGGER.debug('%s - Channel is live', name)
        regex = r"\"width\":48,\"height\":48},{\"url\":\"(.*?)\",\"width\":88,\"height\":88},{\"url\":"
        channel_image = re.findall(regex, info, re.MULTILINE)[0].replace("=s88-c-k-c0x00ffffff-no-rj", "")
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.debug('%s - Could not update - %s', name, error)
    return live, channel_image

async def is_youtube_short(video_id, name, session):
    """Check if a video is a YouTube Short with stricter validation to reduce false positives"""
    try:
        # Controlla la pagina normale del video
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        async with async_timeout.timeout(10):
            response = await session.get(video_url, cookies=dict(CONSENT="YES+cb"))
            info = await response.text()
        
        # Indicatori SPECIFICI che un video è uno Short
        # Questi sono più affidabili e riducono i falsi positivi
        definitive_short_indicators = [
            '"isShort":true',                      # Indicatore JSON esplicito
            '"shorts":{"isShort":true',            # Struttura JSON specifica per Shorts
            'ytd-shorts-player',                   # Player specifico per Shorts
            '"webPageType":"WEB_PAGE_TYPE_SHORTS"' # Tipo di pagina esplicito
        ]
        
        # Prima verifica: cerca indicatori definitivi
        for indicator in definitive_short_indicators:
            if indicator in info:
                _LOGGER.debug('%s - Video %s confirmed as YouTube Short (indicator: %s)', name, video_id, indicator)
                return True
        
        # Seconda verifica: controlla durata E altri segnali insieme
        duration_match = re.search(r'"lengthSeconds":"(\d+)"', info)
        if duration_match:
            duration = int(duration_match.group(1))
            
            # Solo se la durata è <= 180 secondi E ci sono altri indicatori
            if duration <= 180:
                additional_indicators = [
                    'shorts',  # parola "shorts" nel contenuto
                    '"isShortsMobileWeb":true',  # indicatore mobile
                    'shortsLockupViewModel'  # componente UI specifico
                ]
                
                for indicator in additional_indicators:
                    if indicator in info.lower():
                        _LOGGER.debug('%s - Video %s is YouTube Short (duration: %ds + indicator: %s)', 
                                    name, video_id, duration, indicator)
                        return True
                
                # Se è molto corto (< 30 sec) e non ci sono indicatori contrari, probabilmente è uno Short
                if duration <= 30:
                    # Verifica che non sia un video normale molto corto o live
                    normal_video_indicators = ['"isLive":true', '"isLiveBroadcast":true']
                    if not any(indicator in info for indicator in normal_video_indicators):
                        _LOGGER.debug('%s - Video %s likely Short (very short duration: %ds)', name, video_id, duration)
                        return True
        
        _LOGGER.debug('%s - Video %s is NOT a YouTube Short', name, video_id)
        return False
        
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.debug('%s - Could not check if video is Short - %s', name, error)
        return False

# Versione ancora più conservativa (opzionale - usa solo se hai ancora falsi positivi)
async def is_youtube_short_strict(video_id, name, session):
    """Very strict Short detection - only when absolutely sure"""
    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        async with async_timeout.timeout(10):
            response = await session.get(video_url, cookies=dict(CONSENT="YES+cb"))
            info = await response.text()
        
        # Solo gli indicatori più affidabili
        strict_indicators = [
            '"isShort":true',
            '"webPageType":"WEB_PAGE_TYPE_SHORTS"',
            'ytd-shorts-player'
        ]
        
        for indicator in strict_indicators:
            if indicator in info:
                _LOGGER.debug('%s - Video %s is definitely a YouTube Short', name, video_id)
                return True
        
        # Nessun altro controllo - solo questi indicatori certi
        return False
        
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.debug('%s - Could not check if video is Short - %s', name, error)
        return False