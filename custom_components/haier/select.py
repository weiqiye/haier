import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import async_register_entity
from .core.attribute import HaierAttribute
from .core.device import HaierDevice
from .entity import HaierAbstractEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    await async_register_entity(
        hass,
        entry,
        async_add_entities,
        Platform.SELECT,
        lambda device, attribute: HaierSelect(device, attribute)
    )


class HaierSelect(HaierAbstractEntity, SelectEntity):

    def __init__(self, device: HaierDevice, attribute: HaierAttribute):
        super().__init__(device, attribute)

        if 'value_comparison_table' not in attribute.ext.keys():
            raise ValueError('value_comparison_table must exist')

    def _update_value(self):
        data_key = self._attribute.ext.get('data_key', self._attribute.key)
        self._attr_current_option = self._get_value_from_comparison_table(self._attributes_data[data_key])

    def select_option(self, option: str) -> None:
        data_key = self._attribute.ext.get('data_key', self._attribute.key)
        self._send_command({
            data_key: self._get_value_from_comparison_table(option)
        })

    def _get_value_from_comparison_table(self, value):
        value_comparison_table = self._attribute.ext.get('value_comparison_table', {})

        # 部分设备的列表型属性（如 heatingMode）在无激活模式时会上报空列表 []，
        # 此时没有可对应的选项，直接返回 None 表示未选中，避免打印无意义的告警。
        if isinstance(value, list):
            if not value:
                return None
            # 单元素列表取首元素再查表，兼容设备以列表形式返回单个取值的情况
            value = value[0]

        if value in (None, ''):
            return None

        if str(value) not in value_comparison_table:
            _LOGGER.warning('Device [{}] attribute [{}] value [{}] not recognizable'.format(
                self._device.id, self._attribute.key, value
            ))
            return value

        return value_comparison_table.get(str(value))
