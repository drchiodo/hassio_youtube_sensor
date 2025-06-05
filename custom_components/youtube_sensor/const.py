"""Constants for the YouTube Sensor integration."""

DOMAIN = "youtube_sensor"

CONF_CHANNEL_ID = "channel_id"
CONF_INCLUDE_SHORTS = "includeShorts"

ICON = "mdi:youtube"

BASE_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
CHANNEL_LIVE_URL = "https://www.youtube.com/channel/{}"
SHORTS_URL = "https://www.youtube.com/shorts/{}"