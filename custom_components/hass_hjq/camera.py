"""Support for HeJiaQin Cameras."""

import asyncio
import logging
import time

import aiohttp
from haffmpeg.tools import IMAGE_JPEG
from homeassistant.components.camera import Camera, CameraEntityFeature
from homeassistant.components.ffmpeg import async_get_image
from homeassistant.components.stream import Stream
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .hjqapi import HJQApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up HeJiaQin cameras."""
    hejiaqin_api: HJQApi = hass.data[DOMAIN][entry.entry_id]
    await hejiaqin_api.get_video_auth()
    cameras = await hejiaqin_api.get_camera_info()
    # entities = [HeJiaQinCamera(hass, camera, hejiaqin_api) for camera in cameras]
    entities = []
    for camera in cameras:
        dev_info = await hejiaqin_api.get_device_info(
            camera["baseUrl"], camera["jwtoken"], camera["mac_id"]
        )
        e = HeJiaQinCamera(hass, camera, dev_info, hejiaqin_api)
        entities.append(e)
    async_add_entities(entities)

    hass.async_add_hass_job


class HeJiaQinCamera(Camera):
    """Representation of a HeJiaQin Camera."""

    _attr_is_streaming = True

    def __init__(self, hass, camera, dev_info, api):
        """Initialize the camera."""
        super().__init__()
        self.hass = hass
        self._camera = camera
        self._dev_info = dev_info
        self._api: HJQApi = api
        self._name = camera["mac_name"]
        self._unique_id = camera["mac_id"]
        self._attr_available = True
        self._stream_source = None
        self._attr_supported_features = CameraEntityFeature.STREAM
        self._stop_task = False
        # self.hass.async_create_background_task(self.keep_live_addr(), "keep")
        # asyncio.create_task(self.keep_live_addr())

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._unique_id

    @property
    async def use_stream_for_stills(self):
        return True

    @property
    def use_stream_for_stills(self):
        return True

    @property
    def device_info(self):
        """Return device info for this camera."""
        # return {
        #     "identifiers": {(DOMAIN, self._unique_id)},
        #     "name": self._name,
        #     # "manufacturer": self._manufacturer,
        #     # "model": self._model,
        #     # "sw_version": self._camera.get("firmware_version", "Unknown"),
        # }
        # print(self._dev_info)

        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer=self._dev_info["mac_model"],
            model=self._dev_info["mac_model"],
            sw_version=self._dev_info["firmware_model"],
        )

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the camera."""
        return {
            "ip_address": self._dev_info["ip_address"],  # 自定义字段：设备的 IP 地址
            "mac_address": self._dev_info["mac_addr"],  # 设备的 MAC 地址
        }

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        # 实体启用时启动保活任务
        self.hass.async_create_task(self.keep_live_addr())

    async def async_will_remove_from_hass(self):
        """Stop the task when entity is removed."""
        # 实体被禁用或删除时停止保活任务
        _LOGGER.info(f"{self._camera['mac_name']} 实体被禁用或删除时停止保活任务")
        self._stop_task = True
        if self.stream :
            await self.stream.stop()
            self.stream = None

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a still image response from the camera."""
        return await async_get_image(
            self.hass,
            self._input,
            output_format=IMAGE_JPEG,
        )

    async def async_create_stream(self) -> Stream | None:
        """
        Create a Stream for stream_source.
        Full name: homeassistant.components.camera.Camera.async_create_stream
        """
        _LOGGER.info(f"{self._camera['mac_name']} 开始获取直播流...... {self._stream_source}")
        try:
            if self.stream:
                await self.stream.stop()
            self.stream = None
            self.stream = await super().async_create_stream()
            self.stream.dynamic_stream_settings.preload_stream = True
            # if not await self.check_live_addr():
            #     await self.async_update()
            #     _LOGGER.info(f"视频地址已过期, 更新播放地址: {self._stream_source}")
            return self.stream
        except Exception as e:
            _LOGGER.error(f"Error opening stream for {self._name}: {e}")
            return self.stream

    async def stream_source(self) -> str | None:
        if self._stream_source is None:
            addr = await self._api.get_live_addr(
                self._camera["baseUrl"], self._camera["jwtoken"], self._camera["mac_id"]
            )
            _LOGGER.info(f"{self._camera["mac_name"]} 获取到直播流：{addr}")
            self._stream_source = addr
        return self._stream_source

    async def async_update(self):
        return

    async def check_live_addr(self) -> bool:
        timeout = aiohttp.ClientTimeout(total=1)
        code = 0
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(self._stream_source) as response:
                    code = response.status
            except Exception:
                code = 404
            return code == 200

    async def keep_live_addr(self):
        """Continuously keep the live address alive."""
        await asyncio.sleep(3)  # 初始等待时间
        _LOGGER.info(f"{self._camera['mac_name']} 开始保活 {self._stream_source}")

        while not self._stop_task:
            if not self.enabled:
                _LOGGER.info(f"{self._camera['mac_name']} 已被禁用，停止保活循环")
                break
            if not self._stream_source:
                _LOGGER.warning(f"{self._camera['mac_name']} 播放地址为空，等待重试...")
                await asyncio.sleep(10)  # 如果流地址为空，等待 10 秒后重试
                continue

            if self.hass.states.get(self.entity_id) is None:
                _LOGGER.info(f"{self._camera['mac_name']} 已被删除，停止保活循环")
                break

            # 检查直播地址是否有效
            if not await self.check_live_addr():
                _LOGGER.warning(
                    f"{self._camera['mac_name']} 播放地址无效，更新地址中..."
                )
                # 获取并更新新的流地址
                cameras = await self._api.get_camera_info()
                self._camera = [
                    c for c in cameras if c["mac_id"] == self._camera["mac_id"]
                ][0]

                addr = await self._api.get_live_addr(
                    self._camera["baseUrl"],
                    self._camera["jwtoken"],
                    self._camera["mac_id"],
                )
                if addr is not None:
                    self._stream_source = addr
                    self.stream.update_source(addr)
                    _LOGGER.info("{self._camera['mac_name']} 更新播放地址为: {self._stream_source}")

            # 调用 API 保持地址活跃状态
            await self._api.keep_live_addr(
                self._camera["baseUrl"], self._camera["jwtoken"], self._camera["mac_id"]
            )
            _LOGGER.debug(f"{self._camera['mac_name']} 正在保活")

            await asyncio.sleep(20)  # 保活后每 10 秒执行一次
