# Home Assistant - Sengled Bulb Integration

This is a custom component to allow control of Sengled Bulbs in Homeassistant using the unofficial Sengled API. Please note this mimics the Sengled app and therefore Sengled may cut off access at anytime.

### Highlights of what **SengledApi** can do

* Control Sengled Bulbs as lights through HA

### Potential Downsides

* This is an unofficial implementation of the api and therefore may be disabled or broken at anytime by Sengled
* I only have Element Classic A19 Kit (Light bulbs + Hub) to test https://us.sengled.com/products/element-classic-kit
* An update may break them without my knowledge. **Please use the betas as they become avaliable**

## Installation (HACS) - Highly Recommended

1. Have HACS installed, this will allow you to easily update
2. Add [https://github.com/jfarmer08/ha-sengledapi](https://github.com/jfarmer08/ha-sengledapi) as a custom repository as Type: Integration
3. Click install under "Sengled Bulb Integration" in the Integration tab
4. Restart HA

## Installation (Manual)

1. Download this repository as a ZIP (green button, top right) and unzip the archive
2. Copy `/custom_components/sengledapi` to your `<config_dir>/` directory
   * On Hassio the final location will be `/config/custom_components/sengledapi`
   * On Hassbian the final location will be `/home/homeassistant/.homeassistant/custom_components/sengledapi`
3. Restart HA

## Configuration

Add the following to your configuration file.

```yaml
sengledapi:
  username: <email for sengled>
  password: <password for sengled>
```

## Usage

* Restart HA

* Entities will show up as `light.<friendly name>` for example (`light.livingroom_lamp`).

## Reporting an Issue

1. Setup your logger to print debug messages for this component by adding this to your `configuration.yaml`:
    ```yaml
    logger:
      default: warning
      logs:
        custom_components.sengledapi: debug
    ```
2. Restart HA
3. Verify you're still having the issue
4. File an issue in this Github Repository

<a href="https://www.buymeacoffee.com/jfarmer08" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-red.png" alt="Buy Me A Coffee" style="height: 51px !important;width: 217px !important;" ></a>
