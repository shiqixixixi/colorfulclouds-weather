import logging
import json
import time
from datetime import datetime, timedelta
from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    WeatherEntity,
)
from homeassistant.const import (
    CONF_NAME,
    LENGTH_INCHES,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
    LENGTH_MILLIMETERS,
    PRESSURE_HPA,
    PRESSURE_INHG,
    SPEED_KILOMETERS_PER_HOUR,
    SPEED_MILES_PER_HOUR,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
from .const import (
    ATTRIBUTION,
    COORDINATOR,
    ROOT_PATH,
    DOMAIN,
    NAME,
    MANUFACTURER,
    CONF_LIFEINDEX,
)

PARALLEL_UPDATES = 1
_LOGGER = logging.getLogger(__name__)

CONDITION_MAP = {
    'CLEAR_DAY': 'sunny',
    'CLEAR_NIGHT': 'clear-night',
    'PARTLY_CLOUDY_DAY': 'partlycloudy',
    'PARTLY_CLOUDY_NIGHT':'partlycloudy',
    'CLOUDY': 'cloudy',
    'LIGHT_HAZE': 'fog',
    'MODERATE_HAZE': 'fog',
    'HEAVY_HAZE': 'fog',
    'LIGHT_RAIN': 'rainy',
    'MODERATE_RAIN': 'rainy',
    'HEAVY_RAIN': 'pouring',
    'STORM_RAIN': 'pouring',
    'FOG': 'fog',
    'LIGHT_SNOW': 'snowy',
    'MODERATE_SNOW': 'snowy',
    'HEAVY_SNOW': 'snowy',
    'STORM_SNOW': 'snowy',
    'DUST': 'fog',
    'SAND': 'fog',
    'THUNDER_SHOWER': 'lightning-rainy',
    'HAIL': 'hail',
    'SLEET': 'snowy-rainy',
    'WIND': 'windy',
    'HAZE': 'fog',
    'RAIN': 'rainy',
    'SNOW': 'snowy',
}

TRANSLATE_SUGGESTION = {
    'AnglingIndex': '钓鱼指数',
    'AirConditionerIndex': '空调开机指数',
    'AllergyIndex': '过敏指数',
    'HeatstrokeIndex': '中暑指数',
    'RainGearIndex': '雨具指数',
    'DryingIndex': '晾晒指数',
    'WindColdIndex': '风寒指数',
    'KiteIndex': '风筝指数',
    'MorningExerciseIndex': '晨练指数',
    'UltravioletIndex': '紫外线指数',
    'DrinkingIndex': '饮酒指数',
    'ComfortIndex': '舒适指数',
    'CarWashingIndex': '洗车指数',
    'DressingIndex': '穿衣指数',
    'ColdRiskIndex': '感冒指数',
    'AQIIndex': '空气污染指数',
    'WashClothesIndex': '洗衣指数',
    'MakeUpIndex': '化妆指数',
    'MoodIndex': '情绪指数',
    'SportIndex': '运动指数',
    'TravelIndex': '旅游指数',
    'DatingIndex': '交友指数',
    'ShoppingIndex': '逛街指数',
    'HairdressingIndex': '美发指数',
    'NightLifeIndex': '夜生活',
    'BoatingIndex': '划船指数',
    'RoadConditionIndex': '路况指数',
    'TrafficIndex': '交通指数',
    'ultraviolet': '紫外线',
    'carWashing': '洗车指数',
    'dressing': '穿衣指数',
    'comfort': '舒适度指数',
    'coldRisk': '感冒指数',
}

ATTR_SUGGESTION = "suggestion"

async def async_setup_entry(hass, config_entry, async_add_entities):    
    """Add a Colorfulclouds weather entity from a config_entry."""
    name = config_entry.data[CONF_NAME]
    life = config_entry.options.get(CONF_LIFEINDEX, False)

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    _LOGGER.debug("metric: %s", coordinator.data["is_metric"])

    async_add_entities([ColorfulCloudsEntity(name, life, coordinator)], False)
            
class ColorfulCloudsEntity(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, name, life, coordinator):
        
        self.coordinator = coordinator
        _LOGGER.debug("coordinator: %s", coordinator.data["server_time"])
        self._name = name
        self.life = life
        self._attrs = {}
        # self._unit_system = "Metric" if self.coordinator.data["is_metric"]=="metric:v2" else "Imperial"
        # Coordinator data is used also for sensors which don't have units automatically
        # converted, hence the weather entity's native units follow the configured unit
        # system
        if self.coordinator.data["is_metric"]=="metric:v2":
            self._attr_native_precipitation_unit = LENGTH_MILLIMETERS
            self._attr_native_pressure_unit = PRESSURE_HPA
            self._attr_native_temperature_unit = TEMP_CELSIUS
            self._attr_native_visibility_unit = LENGTH_KILOMETERS
            self._attr_native_wind_speed_unit = SPEED_KILOMETERS_PER_HOUR
            self._unit_system = "Metric"
        else:
            self._unit_system = "Imperial"
            self._attr_native_precipitation_unit = LENGTH_INCHES
            self._attr_native_pressure_unit = PRESSURE_INHG
            self._attr_native_temperature_unit = TEMP_FAHRENHEIT
            self._attr_native_visibility_unit = LENGTH_MILES
            self._attr_native_wind_speed_unit = SPEED_MILES_PER_HOUR
        

    @property
    def name(self):
        return self._name
        
    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION
        
    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        _LOGGER.debug("weather_unique_id: %s", self.coordinator.data["location_key"])
        return self.coordinator.data["location_key"]

    @property
    def device_info(self):
        """Return the device info."""
        info = {
            "identifiers": {(DOMAIN, self.coordinator.data["location_key"])},
            "name": self._name,
            "manufacturer": MANUFACTURER,
        }        
        from homeassistant.helpers.device_registry import DeviceEntryType
        info["entry_type"] = DeviceEntryType.SERVICE        
        return info

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        #return self.coordinator.last_update_success
        return (int(datetime.now().timestamp()) - int(self.coordinator.data["server_time"]) < 1800)
        
    @property
    def condition(self):
        """Return the weather condition."""
        skycon = self.coordinator.data["result"]["realtime"]["skycon"]
        return CONDITION_MAP[skycon]

    @property
    def native_temperature(self):
        return self.coordinator.data["result"]['realtime']['temperature']

    @property
    def humidity(self):
        return float(self.coordinator.data["result"]['realtime']['humidity']) * 100

    @property
    def native_wind_speed(self):
        """风速"""
        return self.coordinator.data["result"]['realtime']['wind']['speed']

    @property
    def wind_bearing(self):
        """风向"""
        return self.coordinator.data["result"]['realtime']['wind']['direction']

    @property
    def native_visibility(self):
        """能见度"""
        return self.coordinator.data["result"]['realtime']['visibility']

    @property
    def native_pressure(self):
        return round(float(self.coordinator.data["result"]['realtime']['pressure'])/100)

    @property
    def pm25(self):
        """pm25，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['pm25']

    @property
    def pm10(self):
        """pm10，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['pm10']

    @property
    def o3(self):
        """臭氧，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['o3']

    @property
    def no2(self):
        """二氧化氮，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['no2']

    @property
    def so2(self):
        """二氧化硫，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['so2']

    @property
    def co(self):
        """一氧化碳，质量浓度值"""
        return self.coordinator.data["result"]['realtime']['air_quality']['co']

    @property
    def aqi(self):
        """AQI（国标）"""
        return self.coordinator.data["result"]['realtime']['air_quality']['aqi']['chn']

    @property
    def aqi_description(self):
        """AQI（国标）"""
        return self.coordinator.data["result"]['realtime']['air_quality']['description']['chn']

    @property
    def aqi_usa(self):
        """AQI USA"""
        return self.coordinator.data["result"]['realtime']['air_quality']['aqi']['usa']
    
    @property
    def aqi_usa_description(self):
        """AQI USA"""
        return self.coordinator.data["result"]['realtime']['air_quality']['description']['usa']
    
    @property
    def forecast_hourly(self):
        """实时天气预报描述-小时"""
        return self.coordinator.data['result']['hourly']['description']

    @property
    def forecast_minutely(self):
        """实时天气预报描述-分钟"""
        return self.coordinator.data['result']['minutely']['description']

    @property
    def forecast_minutely_probability(self):
        """分钟概率"""
        return self.coordinator.data['result']['minutely']['probability']

    @property
    def forecast_alert(self):
        """天气预警"""
        alert = self.coordinator.data['result']['alert'] if 'alert' in self.coordinator.data['result'] else ""
        return alert
        
    @property
    def forecast_keypoint(self):
        """实时天气预报描述-注意事项"""
        return self.coordinator.data['result']['forecast_keypoint']        
        
    @property
    def updatetime(self):
        """实时天气预报获取时间."""
        return datetime.fromtimestamp(self.coordinator.data['server_time'])    
        
    @property
    def state_attributes(self):
        _LOGGER.debug(self.coordinator.data)
        data = super(ColorfulCloudsEntity, self).state_attributes
        data['forecast_hourly'] = self.forecast_hourly
        data['forecast_minutely'] = self.forecast_minutely
        data['forecast_probability'] = self.forecast_minutely_probability
        data['forecast_keypoint'] = self.forecast_keypoint
        data['forecast_alert'] = self.forecast_alert
        data['pm25'] = self.pm25
        data['pm10'] = self.pm10
        data['skycon'] = self.coordinator.data['result']['realtime']['skycon']
        data['o3'] = self.o3
        data['no2'] = self.no2
        data['so2'] = self.so2
        data['co'] = self.co
        data['aqi'] = self.aqi
        data['aqi_description'] = self.aqi_description
        data['aqi_usa'] = self.aqi_usa
        data['aqi_usa_description'] = self.aqi_usa_description
        data['update_time'] = self.updatetime

        data['hourly_precipitation'] = self.coordinator.data['result']['hourly']['precipitation']
        data['hourly_temperature'] = self.coordinator.data['result']['hourly']['temperature']
        data['hourly_cloudrate'] = self.coordinator.data['result']['hourly']['cloudrate']
        data['hourly_skycon'] = self.coordinator.data['result']['hourly']['skycon']
        data['hourly_wind'] = self.coordinator.data['result']['hourly']['wind']
        data['hourly_visibility'] = self.coordinator.data['result']['hourly']['visibility']
        data['hourly_aqi'] = self.coordinator.data['result']['hourly']['air_quality']['aqi']
        data['hourly_pm25'] = self.coordinator.data['result']['hourly']['air_quality']['pm25']
        
        if self.life == True:
            data[ATTR_SUGGESTION] = [{'title': k, 'title_cn': TRANSLATE_SUGGESTION.get(k,k), 'brf': v.get('desc'), 'txt': v.get('detail')} for k, v in self.coordinator.data['lifeindex'].items()]
            data["custom_ui_more_info"] = "colorfulclouds-weather-more-info"        
        return data  

    @property
    def forecast(self):
        forecast_data = []
        for i in range(len(self.coordinator.data['result']['daily']['temperature'])):
            time_str = self.coordinator.data['result']['daily']['temperature'][i]['date'][:10]
            data_dict = {
                ATTR_FORECAST_TIME: datetime.strptime(time_str, '%Y-%m-%d'),
                ATTR_FORECAST_CONDITION: CONDITION_MAP[self.coordinator.data['result']['daily']['skycon'][i]['value']],
                "skycon": self.coordinator.data['result']['daily']['skycon'][i]['value'],
                ATTR_FORECAST_NATIVE_PRECIPITATION: self.coordinator.data['result']['daily']['precipitation'][i]['avg'],
                ATTR_FORECAST_NATIVE_TEMP: self.coordinator.data['result']['daily']['temperature'][i]['max'],
                ATTR_FORECAST_NATIVE_TEMP_LOW: self.coordinator.data['result']['daily']['temperature'][i]['min'],
                ATTR_FORECAST_WIND_BEARING: self.coordinator.data['result']['daily']['wind'][i]['avg']['direction'],
                ATTR_FORECAST_NATIVE_WIND_SPEED: self.coordinator.data['result']['daily']['wind'][i]['avg']['speed']
            }
            forecast_data.append(data_dict)

        return forecast_data

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update Colorfulclouds entity."""
        await self.coordinator.async_request_refresh()
        