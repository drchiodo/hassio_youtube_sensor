"""
A platform which give you info about the newest video on a channel with option to include/exclude Shorts.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/youtube
"""

import logging
import async_timeout
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from dateutil.parser import parse
from homeassistant.const import CONF_NAME
import re
import html
import xml.etree.ElementTree as ET

from .const import (
    DOMAIN,
    CONF_CHANNEL_ID,
    CONF_INCLUDE_SHORTS,
    ICON,
    BASE_URL,
    CHANNEL_LIVE_URL,
    SHORTS_URL,
)

# Manteniamo il supporto per configuration.yaml per retrocompatibilità
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CHANNEL_ID): cv.string,
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_INCLUDE_SHORTS, default=False): cv.boolean,
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up YouTube Sensor from config entry."""
    channel_id = config_entry.data[CONF_CHANNEL_ID]
    name = config_entry.data[CONF_NAME]
    include_shorts = config_entry.data.get(CONF_INCLUDE_SHORTS, False)
    
    session = async_create_clientsession(hass)
    
    async_add_entities([YoutubeSensor(channel_id, name, session, include_shorts)], True)


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):  # pylint: disable=unused-argument
    """Setup sensor platform (legacy configuration.yaml support)."""
    channel_id = config['channel_id']
    custom_name = config.get('name')  # Nome personalizzato opzionale
    include_shorts = config.get('includeShorts', False)  # Parametro per includere Shorts
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
        async_add_entities([YoutubeSensor(channel_id, display_name, session, include_shorts)], True)


class YoutubeSensor(SensorEntity):
    """YouTube Sensor class"""
    def __init__(self, channel_id, name, session, include_shorts=False):
        self._attr_native_value = None
        self.session = session
        self._attr_entity_picture = None
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
        self.include_shorts = include_shorts  # Nuovo parametro
        
        # Attributi per config entry
        self._attr_unique_id = f"youtube_{channel_id}"
        self._attr_name = f"youtube_{name}"
        self._attr_icon = ICON

    async def async_update(self):
        """Update sensor - trova il primo video secondo le impostazioni di includeShorts."""
        if self.include_shorts:
            _LOGGER.debug('%s - Running update (including Shorts)', self._name)
        else:
            _LOGGER.debug('%s - Running update (excluding Shorts)', self._name)
            
        try:
            url = BASE_URL.format(self.channel_id)
            async with async_timeout.timeout(10):
                response = await self.session.get(url)
                info = await response.text()
            
            exp = parse(response.headers['Expires'])
            if exp < self.expiry:
                return
            self.expiry = exp
            
            # Parse XML per trovare tutti i video
            root = ET.fromstring(info)
            
            # Namespace per YouTube XML
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'yt': 'http://www.youtube.com/xml/schemas/2015',
                'media': 'http://search.yahoo.com/mrss/'
            }
            
            # Trova tutte le entry (video)
            entries = root.findall('atom:entry', namespaces)
            
            # Itera attraverso i video per trovare il primo video secondo le impostazioni
            video_found = False
            for entry in entries:
                # Estrai informazioni del video
                video_id_elem = entry.find('yt:videoId', namespaces)
                if video_id_elem is None:
                    continue
                    
                temp_video_id = video_id_elem.text
                
                # Controlla se è uno Short
                is_short = await is_youtube_short(temp_video_id, self._name, self.session)
                
                # Logica di filtro basata su include_shorts
                should_include_video = True
                if not self.include_shorts and is_short:
                    # Se non vogliamo gli Shorts e questo è uno Short, salta
                    should_include_video = False
                    _LOGGER.debug('%s - Skipping Short video: %s', self._name, temp_video_id)
                elif self.include_shorts or not is_short:
                    # Se vogliamo gli Shorts, o se questo non è uno Short, includi
                    should_include_video = True
                
                if should_include_video:
                    # Questo è il primo video che soddisfa i nostri criteri
                    if is_short:
                        _LOGGER.debug('%s - Found Short video: %s', self._name, temp_video_id)
                    else:
                        _LOGGER.debug('%s - Found non-Short video: %s', self._name, temp_video_id)
                    
                    # Estrai titolo
                    title_elem = entry.find('atom:title', namespaces)
                    title = title_elem.text if title_elem is not None else "Unknown Title"
                    
                    # Estrai URL
                    link_elem = entry.find('atom:link[@rel="alternate"]', namespaces)
                    video_url = link_elem.get('href') if link_elem is not None else f"https://www.youtube.com/watch?v={temp_video_id}"
                    
                    # Estrai data pubblicazione
                    published_elem = entry.find('atom:published', namespaces)
                    published_date = published_elem.text if published_elem is not None else None
                    
                    # Estrai thumbnail
                    thumbnail_elem = entry.find('.//media:thumbnail', namespaces)
                    thumbnail_url = thumbnail_elem.get('url') if thumbnail_elem is not None else None
                    
                    # Estrai stars e views
                    stars_elem = entry.find('.//media:starRating', namespaces)
                    stars = stars_elem.get('count') if stars_elem is not None else '0'
                    
                    stats_elem = entry.find('.//media:statistics', namespaces)
                    views = stats_elem.get('views') if stats_elem is not None else '0'
                    
                    # Aggiorna le proprietà dell'oggetto
                    self.url = video_url
                    self.content_id = temp_video_id
                    self.published = published_date
                    self._attr_native_value = html.unescape(title)
                    self._attr_entity_picture = thumbnail_url
                    self.stars = stars
                    self.views = views
                    self.is_short = is_short
                    
                    # Controlla se è live/stream
                    if self.live or video_url != self.url:
                        self.stream, self.live, self.stream_start = await is_live(video_url, self._name, self.hass, self.session)
                    else:
                        _LOGGER.debug('%s - Skipping live check', self._name)
                    
                    video_found = True
                    break
            
            if not video_found:
                if self.include_shorts:
                    _LOGGER.warning('%s - No videos found in feed', self._name)
                else:
                    _LOGGER.warning('%s - No non-Short videos found in feed', self._name)
                
                # Fallback al video più recente se non ci sono video che soddisfano i criteri
                title = info.split('<title>')[2].split('</')[0]
                url = info.split('<link rel="alternate" href="')[2].split('"/>')[0]
                self.url = url
                self.content_id = url.split('?v=')[1]
                self.published = info.split('<published>')[2].split('</')[0]
                thumbnail_url = info.split('<media:thumbnail url="')[1].split('"')[0]
                self._attr_native_value = html.unescape(title)
                self._attr_entity_picture = thumbnail_url
                self.stars = info.split('<media:starRating count="')[1].split('"')[0]
                self.views = info.split('<media:statistics views="')[1].split('"')[0]
                self.is_short = await is_youtube_short(self.content_id, self._name, self.session)
            
            # Controlla lo stato del canale
            channel_url = CHANNEL_LIVE_URL.format(self.channel_id)
            self.channel_live, self.channel_image = await is_channel_live(channel_url, self.name, self.hass, self.session)
            
        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.debug('%s - Could not update - %s', self._name, error)

    @property
    def name(self):
        """Name."""
        return f"youtube_{self._name}"

    @property
    def entity_picture(self):
        """Picture."""
        return self._attr_entity_picture

    @property
    def native_value(self):
        """State."""
        return self._attr_native_value

    @property
    def unique_id(self):
        """Return unique ID for this sensor."""
        return f"youtube_{self.channel_id}"

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
                'include_shorts': self.include_shorts,  # Aggiunto per debug
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
    channel_image = None
    try:
        async with async_timeout.timeout(10):
            response = await session.get(url, cookies=dict(CONSENT="YES+cb"))
            info = await response.text()
        if '{"iconType":"LIVE"}' in info:
            live = True
            _LOGGER.debug('%s - Channel is live', name)
        regex = r"\"width\":48,\"height\":48},{\"url\":\"(.*?)\",\"width\":88,\"height\":88},{\"url\":"
        matches = re.findall(regex, info, re.MULTILINE)
        if matches:
            channel_image = matches[0].replace("=s88-c-k-c0x00ffffff-no-rj", "")
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