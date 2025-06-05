# YouTube Sensor for Home Assistant

A custom sensor for Home Assistant that monitors YouTube channels and provides information about the latest videos, including livestreams and YouTube Shorts. Features a modern **graphical configuration interface** with **multi-language support** for easy setup!

## 🚀 Features

- **🖥️ Graphical Configuration**: Easy setup through Home Assistant's UI (no more YAML editing!)
- **🌍 Multi-language Support**: Interface available in English, Italian, Spanish, French, German, and more
- **📺 Video monitoring**: Track the latest video published on a YouTube channel
- **🔴 Livestream detection**: Detect when a channel is live or when a video is a stream
- **🎬 YouTube Shorts support**: Automatically identify Short videos with option to include/exclude them
- **⚙️ Flexible filtering**: Choose whether to include or exclude YouTube Shorts from monitoring
- **⏱️ Configurable scan interval**: Set custom update frequency (5-120 minutes) for each channel
- **📊 Complete metadata**: Views, stars, publication date, thumbnails
- **🔄 Automatic updates**: Self-updating while respecting YouTube's limits
- **🔧 Migration support**: Automatically imports existing YAML configurations

## 📋 Requirements

- Home Assistant 2021.12.0 or higher
- Active internet connection
- YouTube channel ID you want to monitor

## 🔧 Installation

### Method 1: Manual Installation

1. Download all files from the repository
2. Create the `custom_components/youtube_sensor/` folder in your Home Assistant configuration directory
3. Copy all files (`__init__.py`, `config_flow.py`, `const.py`, `manifest.json`, `sensor.py`, `strings.json`) into the created folder
4. **Optional**: Copy the `translations/` folder for multi-language support
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration**
7. Search for "YouTube Sensor" and click to add

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
13. Go to **Settings → Devices & Services → Add Integration**
14. Search for "YouTube Sensor" and click to add

## ⚙️ Configuration

### 🎯 Graphical Configuration (Recommended)

1. **Navigate to Settings → Devices & Services**
2. **Click "Add Integration"**
3. **Search for "YouTube Sensor"**
4. **Fill out the configuration form:**
   - **Channel ID**: The YouTube channel ID (starts with UC)
   - **Channel Name** (optional): Custom name for your sensor
   - **Include YouTube Shorts**: Toggle to include/exclude Shorts
   - **Scan Interval**: Update frequency in minutes (5-120 minutes)

5. **Click "Submit"** - the integration will validate the channel and create your sensor!

### 🌍 Multi-language Support

The integration interface is available in multiple languages:

- **🇺🇸 English** (default)
- **🇮🇹 Italian** 
- **🇪🇸 Spanish**
- **🇫🇷 French**
- **🇩🇪 German**

The interface automatically adapts to your Home Assistant language settings. Additional languages can be easily added by contributing translation files.

### 📺 Getting the YouTube Channel ID

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

### 📝 Legacy YAML Configuration (Still Supported)

If you prefer YAML configuration, add this to your `configuration.yaml` file:

```yaml
sensor:
  # Basic configuration (excludes Shorts by default, 15min interval)
  - platform: youtube_sensor
    channel_id: UC4V3oCikXeSqYQr0hBMARwg
    name: "Breaking Italy"
  
  # Explicitly exclude Shorts with custom interval
  - platform: youtube_sensor
    channel_id: UCx7EWheHmjCW3vX8K2d09vg
    name: "GeoPop"
    includeShorts: false
    scan_interval: 30  # Check every 30 minutes
  
  # Include Shorts with frequent updates
  - platform: youtube_sensor
    channel_id: UC5fmXZRQS-6xa2kCbCQds8g
    name: "CURIUSS"
    includeShorts: true
    scan_interval: 10  # Check every 10 minutes
```

**Note**: Existing YAML configurations will be automatically detected and can be migrated to the UI if desired.

## 🔧 Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| **Channel ID** | string | Yes | - | YouTube channel ID (starts with UC, 24 characters) |
| **Channel Name** | string | No | Auto-detected | Custom name for the sensor |
| **Include YouTube Shorts** | boolean | No | `false` | Whether to include YouTube Shorts in monitoring |
| **Scan Interval** | integer | No | `15` | Update frequency in minutes (5-120 minutes) |

### 🎬 YouTube Shorts Behavior

- **Include Shorts: OFF** (default): The sensor will find the latest **regular video**, skipping any YouTube Shorts
- **Include Shorts: ON**: The sensor will find the latest **video of any type**, including YouTube Shorts

### ⏱️ Scan Interval Configuration

- **Default**: 15 minutes - Good balance between responsiveness and resource usage
- **Range**: 5-120 minutes - Customize based on channel activity
- **Recommendations**:
  - **High-activity channels** (news, live streamers): 5-10 minutes
  - **Regular channels**: 15-30 minutes
  - **Low-activity channels**: 60-120 minutes

This allows you to have granular control over what type of content triggers your automations and how frequently each channel is monitored.

## 📊 Entities and Attributes

### Entity ID

Sensors are created with the format: `sensor.youtube_[channel_name]`

Examples:

- `sensor.youtube_breaking_italy` 
- `sensor.youtube_geopop`
- `sensor.youtube_curiuss`

### Main State

The sensor state contains the **title of the latest published video** (filtered by your Shorts setting).

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
| `scan_interval_minutes` | Update frequency in minutes |
| `friendly_name` | Original channel name |

## 🎯 Usage Examples

### 1. Basic Lovelace Card

```yaml
type: entity
entity: sensor.youtube_breaking_italy
```

### 2. Custom Card with Image - Requires custom:button-card component

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

### 7. Multi-Channel Dashboard

```yaml
type: vertical-stack
cards:
  - type: custom:button-card
    entity: sensor.youtube_breaking_italy
    name: Breaking Italy
    show_entity_picture: true
  - type: custom:button-card
    entity: sensor.youtube_geopop
    name: GeoPop
    show_entity_picture: true
```

## 🔍 Troubleshooting

### Integration Not Found

1. **Verify installation**: Ensure all files are in `custom_components/youtube_sensor/`
2. **Restart Home Assistant** completely
3. **Clear browser cache** and refresh the page
4. **Check logs** for any loading errors

### Setup Errors

**"Invalid channel ID"**
- Channel ID must start with "UC"
- Channel ID must be exactly 24 characters long
- Example: `UC4V3oCikXeSqYQr0hBMARwg`

**"Cannot connect to YouTube channel"**
- Check your internet connection
- Verify the channel exists and is public
- Channel might be temporarily unavailable

**"Already configured"**
- This channel is already being monitored
- Check existing integrations in Settings → Devices & Services

### Sensor Issues

**"No non-Short videos found in feed"**
- This warning appears when "Include Shorts" is OFF but the channel has only posted Shorts recently
- The sensor will fallback to the most recent video regardless of type
- Consider enabling "Include Shorts" if the channel posts many Shorts

**"Scan interval too frequent"**
- If you set the scan interval too low (< 5 minutes), it will be automatically adjusted
- Very frequent updates may trigger YouTube rate limiting
- Consider increasing the interval if you experience connection issues

**Sensor shows "Unknown" or "Unavailable"**
- Temporary connection issues
- YouTube may have changed page structure
- YouTube rate limiting - wait and it should recover

### Migration from YAML

**Existing sensors disappeared**
- After installing the integration, existing YAML sensors are replaced
- Re-add channels through the UI configuration
- Your automations will work with the new entity IDs

### Debug

To enable debug logging, add to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.youtube_sensor: debug
```

Debug logs will show:
- Integration setup process
- Channel validation results
- Whether Shorts are being included or excluded
- Which videos are being skipped and why
- Video detection results
- Actual scan intervals being used

## 🛠️ Management

### Adding More Channels

1. Go to **Settings → Devices & Services**
2. Find "YouTube Sensor" and click **"Configure"**
3. Click **"Add Entry"** to add another channel

### Modifying Existing Channels

1. Go to **Settings → Devices & Services**
2. Find your YouTube channel entry
3. Click **"Configure"** to modify settings

### Removing Channels

1. Go to **Settings → Devices & Services**
2. Find your YouTube channel entry
3. Click the **three dots** and select **"Delete"**

## 🌍 Contributing Translations

We welcome translations for additional languages! Here's how to contribute:

### File Structure
```
custom_components/youtube_sensor/
├── strings.json          # English (default)
└── translations/
    ├── it.json           # Italian
    ├── es.json           # Spanish  
    ├── fr.json           # French
    ├── de.json           # German
    └── [your_lang].json  # Your language
```

### Supported Languages
Currently available translations:
- 🇺🇸 **English** (`en`) - Default
- 🇮🇹 **Italian** (`it`) - Complete
- 🇪🇸 **Spanish** (`es`) - Complete  
- 🇫🇷 **French** (`fr`) - Complete
- 🇩🇪 **German** (`de`) - Complete

### Adding a New Language

1. **Copy the English template** from `strings.json`
2. **Create** `translations/[language_code].json`
3. **Translate all text strings** while keeping the JSON structure
4. **Submit a pull request** with your translation

### Language Codes
Use standard ISO 639-1 language codes:
- `pt` = Portuguese
- `nl` = Dutch  
- `ru` = Russian
- `zh` = Chinese
- `ja` = Japanese
- `ko` = Korean
- `sv` = Swedish
- `no` = Norwegian
- `da` = Danish
- `fi` = Finnish

### Translation Guidelines
- Keep technical terms like "Channel ID" consistent
- Maintain the same tone (helpful and professional)
- Test your translation by changing Home Assistant language settings
- Ensure special characters are properly escaped in JSON

## ⚡ Performance and Limits

- **Update frequency**: Configurable per sensor (5-120 minutes)
- **Default interval**: 15 minutes for optimal balance
- **Rate limiting**: YouTube may limit too frequent requests - increase interval if needed
- **Timeout**: Requests timeout after 10 seconds to prevent blocking
- **Shorts detection**: Additional HTTP request per video to determine if it's a Short
- **Concurrent sensors**: No limit on number of channels, but consider total request volume
- **Concurrent sensors**: No limit on number of channels you can monitor

## 🆘 Support

If you encounter issues:

1. **Check the integration status** in Settings → Devices & Services
2. **Verify your configuration** through the UI
3. **Enable debug logging** to see detailed operation
4. **Check Home Assistant logs** for specific errors
5. **Try with a different channel** to isolate issues
6. **Report bugs** on GitHub with debug logs

## 📝 Changelog

### v2.1.0 - Performance & Customization Update! ⚡

- **NEW**: Configurable scan interval (5-120 minutes) per channel
- **NEW**: Smart update frequency recommendations based on channel activity
- **NEW**: Scan interval visible in sensor attributes for monitoring
- **IMPROVED**: Better resource management with customizable polling
- **IMPROVED**: Enhanced logging with scan interval information
- **IMPROVED**: Optimal balance between responsiveness and YouTube rate limits

### v2.0.0 - Major Update! 🎉

- **NEW**: Full graphical configuration interface (Config Flow)
- **NEW**: Multi-language support (English, Italian, Spanish, French, German)
- **NEW**: Modern Home Assistant integration architecture
- **NEW**: Automatic migration from YAML configurations
- **NEW**: Real-time channel validation during setup
- **NEW**: Prevention of duplicate channel configurations
- **NEW**: Enhanced error handling with descriptive messages
- **IMPROVED**: Entity IDs now use channel ID for better uniqueness
- **IMPROVED**: Support for both UI and YAML configuration methods
- **IMPROVED**: Better integration management and removal

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

**🎯 Now with configurable scan intervals, multi-language support, and modern UI configuration!**