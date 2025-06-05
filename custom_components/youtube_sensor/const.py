"""Constants for the YouTube Sensor integration."""

DOMAIN = "youtube_sensor"

CONF_CHANNEL_ID = "channel_id"
CONF_INCLUDE_SHORTS = "includeShorts"
CONF_SCAN_INTERVAL = "scan_interval"

ICON = "mdi:youtube"

# Default scan interval in minutes
DEFAULT_SCAN_INTERVAL = 15

# Min/Max scan intervals in minutes
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 120

BASE_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"
CHANNEL_LIVE_URL = "https://www.youtube.com/channel/{}"
SHORTS_URL = "https://www.youtube.com/shorts/{}"