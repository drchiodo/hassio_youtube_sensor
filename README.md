# YouTube Sensor for Home Assistant

A custom sensor for Home Assistant that monitors YouTube channels and provides information about the latest videos, including livestreams and YouTube Shorts.

## 🚀 Features

- **Video monitoring**: Track the latest video published on a YouTube channel
- **Livestream detection**: Detect when a channel is live or when a video is a stream
- **YouTube Shorts support**: Automatically identify Short videos with option to include/exclude them
- **Flexible filtering**: Choose whether to include or exclude YouTube Shorts from monitoring
- **Complete metadata**: Views, stars, publication date, thumbnails
- **Automatic updates**: Self-updating while respecting YouTube's limits

## 📋 Requirements

- Home Assistant 2021.12.0 or higher
- Active internet connection
- YouTube channel ID you want to monitor

## 🔧 Installation

### Method 1: Manual Installation

1. Download the `sensor.py` file
2. Create the `custom_components/youtube_sensor/` folder in your Home Assistant configuration directory
3. Copy the `sensor.py` file into the created folder
4. Restart Home Assistant

### Method 2: Via HACS

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu (⋮) in the top right corner
4. Select "Custom repositories"
5. Add the repository URL: `https://github.com/drchiodo/hassio_youtube_sensor`
6. Select "Integration" as the category
7. Click "ADD"
8. Close the custom repositories dialog
9. Click "EXPLORE & DOWNLOAD REPOSITORIES"
10. Search for "YouTube Sensor"
11. Click "DOWNLOAD" and then "DOWNLOAD" again
12. Restart Home Assistant

## ⚙️ Configuration

### 1. Getting the YouTube Channel ID

To find the YouTube channel ID:

**Method A - From channel URL:**

- If the URL is `https://www.youtube.com/channel/UC4V3oCikXeSqYQr0hBMARwg`
- The ID is: `UC4V3oCikXeSqYQr0hBMARwg`

**Method B - From username:**

- Go to any video from the channel
- Click on the channel name
- The channel page URL will contain the ID after `/channel/`

**Method C - Online tools:**

- Use sites like `commentpicker.com/youtube-channel-id.php`
- Enter the channel URL to get the ID

### 2. Home Assistant Configuration

Add the configuration to your `configuration.yaml` file:

```yaml
sensor:
  # Basic configuration (excludes Shorts by default)
  - platform: youtube_sensor
    channel_id: UC4V3oCikXeSqYQr0hBMARwg
    name: "Breaking Italy"
  
  # Explicitly exclude Shorts
  - platform: youtube_sensor
    channel_id: UCx7EWheHmjCW3vX8K2d09vg
    name: "GeoPop"
    includeShorts: false
  
  # Include Shorts in monitoring
  - platform: youtube_sensor
    channel_id: UC5fmXZRQS-6xa2kCbCQds8g
    name: "CURIUSS"
    includeShorts: true
```

### 3. Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `platform` | string | Yes | - | Must be `youtube_sensor` |
| `channel_id` | string | Yes | - | YouTube channel ID (starts with UC) |
| `name` | string | No | Channel name | Custom name for the sensor |
| `includeShorts` | boolean | No | `false` | Whether to include YouTube Shorts in monitoring |

### 4. YouTube Shorts Behavior

- **`includeShorts: false`** (default): The sensor will find the latest **regular video**, skipping any YouTube Shorts
- **`includeShorts: true`**: The sensor will find the latest **video of any type**, including YouTube Shorts

This allows you to have granular control over what type of content triggers your automations.

### 5. Restart

After adding the configuration, restart Home Assistant.

## 📊 Entities and Attributes

### Entity ID

Sensors are created with the format: `sensor.youtube_[name]`

Examples:

- `sensor.youtube_breaking_italy`
- `sensor.youtube_geopop`
- `sensor.youtube_curiuss`

### Main State

The sensor state contains the **title of the latest published video** (filtered by your `includeShorts` setting).

### Available Attributes

| Attribute | Description |
|-----------|-------------|
| `url` | Complete video URL |
| `content_id` | Unique YouTube video ID |
| `published` | Publication date and time |
| `stars` | Number of stars/rating |
| `views` | Number of views |
| `stream` | `true` if the video is a stream |
| `live` | `true` if the stream is currently live |
| `stream_start` | Stream start date/time |
| `channel_is_live` | `true` if the channel is live |
| `channel_image` | Channel image URL |
| `is_short` | `true` if the video is a YouTube Short |
| `include_shorts` | Configuration setting for this sensor |
| `friendly_name` | Original channel name |

## 🎯 Usage Examples

### 1. Basic Lovelace Card

```yaml
type: entity
entity: sensor.youtube_breaking_italy
```

### 2. Custom Card with Image - Require custom:button-card component

```yaml
type: custom:button-card
entity: sensor.youtube_breaking_italy
name: Breaking Italy
show_name: true
show_entity_picture: true
entity_picture: |-
  [[[
    return states['sensor.youtube_breaking_italy'].attributes.entity_picture
  ]]]
tap_action:
  action: url
  url_path: |-
    [[[
      return states['sensor.youtube_breaking_italy'].attributes.url
    ]]]
styles:
  card:
    - height: 200px
  name:
    - font-size: 16px
    - font-weight: bold
  entity_picture:
    - border-radius: 10px
```

### 3. Automation for New Videos (Any Type)

```yaml
alias: Announce new video Breaking Italy
description: Send notification when new video is available
triggers:
  - entity_id: sensor.youtube_breaking_italy
    attribute: url
    trigger: state
conditions:
  - condition: template
    value_template: |
      {{ 'watch?v=' in state_attr('sensor.youtube_breaking_italy', 'url') }}
actions:
  - action: notify.mobile_app_ipp
    data:
      message: New video available!
```

### 4. Automation for New Videos (Regular Videos Only)

```yaml
alias: Announce new full video Breaking Italy
description: Send notification when new regular video is available (no Shorts)
triggers:
  - entity_id: sensor.youtube_breaking_italy
    attribute: url
    trigger: state
conditions:
  - condition: template
    value_template: |
      {{ not state_attr('sensor.youtube_breaking_italy', 'is_short') }}
  - condition: template
    value_template: |
      {{ 'watch?v=' in state_attr('sensor.youtube_breaking_italy', 'url') }}
actions:
  - action: notify.mobile_app_ipp
    data:
      message: New full video available!
```

### 5. Automation for YouTube Shorts Only

```yaml
alias: Announce new Short Breaking Italy
description: Send notification when new YouTube Short is available
triggers:
  - entity_id: sensor.youtube_breaking_italy
    attribute: url
    trigger: state
conditions:
  - condition: template
    value_template: |
      {{ state_attr('sensor.youtube_breaking_italy', 'is_short') }}
  - condition: template
    value_template: |
      {{ 'watch?v=' in state_attr('sensor.youtube_breaking_italy', 'url') }}
actions:
  - action: notify.mobile_app_ipp
    data:
      message: New Short available!
```

### 6. Livestream Automation

```yaml
automation:
  - alias: "Breaking Italy is Live"
    trigger:
      - platform: state
        entity_id: sensor.youtube_breaking_italy
        attribute: live
        to: true
    action:
      - service: notify.family
        data:
          title: "🔴 LIVE"
          message: "Breaking Italy is live!"
```

### 7. Multi-Channel Setup with Different Settings

```yaml
sensor:
  # Channel that posts mostly regular videos - exclude Shorts
  - platform: youtube_sensor
    channel_id: UC4V3oCikXeSqYQr0hBMARwg
    name: "Breaking Italy"
    includeShorts: false
  
  # Channel that posts lots of Shorts - include everything
  - platform: youtube_sensor
    channel_id: UCx7EWheHmjCW3vX8K2d09vg
    name: "Tech Shorts"
    includeShorts: true
```

## 🔍 Troubleshooting

### Sensor Doesn't Appear

1. Verify that the channel ID is correct (must start with `UC`)
2. Check Home Assistant logs for errors
3. Make sure the channel is public
4. Restart Home Assistant after changes

### Common Errors

**`Unable to set up`**

- Channel ID is invalid
- Channel doesn't exist or is private
- Internet connection issues

**`Could not update`**

- Temporary connection issues
- YouTube may have changed page structure
- YouTube rate limiting

**`No non-Short videos found in feed`**

- This warning appears when `includeShorts: false` but the channel has only posted Shorts recently
- The sensor will fallback to the most recent video regardless of type
- Consider setting `includeShorts: true` if the channel posts many Shorts

### Debug

To enable debug logging, add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.youtube_sensor: debug
```

Debug logs will show:
- Whether Shorts are being included or excluded
- Which videos are being skipped and why
- Video detection results

## ⚡ Performance and Limits

- **Update frequency**: Sensor respects YouTube's cache headers
- **Rate limiting**: YouTube may limit too frequent requests
- **Timeout**: Requests timeout after 10 seconds to prevent blocking
- **Shorts detection**: Additional HTTP request per video to determine if it's a Short

## 🆘 Support

If you encounter issues:

1. Check Home Assistant logs
2. Verify your configuration
3. Make sure the channel ID is correct
4. Try with a different channel to test
5. Enable debug logging to see detailed operation

## 📝 Changelog

### v1.1.0

- **NEW**: Added `includeShorts` parameter to control YouTube Shorts filtering
- **NEW**: Enhanced logging with separate messages for Shorts inclusion/exclusion
- **NEW**: Added `include_shorts` attribute to sensor for debugging
- **IMPROVED**: Better logic for video filtering based on content type
- **IMPROVED**: More descriptive warning messages when no suitable videos are found

### v1.0.1

- Added YouTube Shorts detection
- Improved livestream detection
- Entity IDs with `youtube_` prefix
- Added `friendly_name` attribute
- Support for live channels
- Improved error handling
- Optimized information parsing

### v1.0.0

- Initial release
- Basic video monitoring
- Livestream support

## 📄 License

This project is released under the MIT License. See the LICENSE file for details.

---

**⭐ If this sensor is useful to you, consider starring the repository!**