import asyncio
import unittest
from unittest.mock import patch

from bluetti_bt_lib.base_devices import BaseDeviceV1, BluettiDevice
from bluetti_bt_lib import DeviceReader
from bluetti_bt_lib.fields import FieldName, SwitchField, NumberField
from bluetti_bt_lib.utils.bleak_client_mock import ClientMockNoEncryption


class TestDeviceReader(unittest.IsolatedAsyncioTestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.ble_mock = ClientMockNoEncryption()

        # Device type
        self.ble_mock.add_r_str(10, "AC300", 6)
        # Serial
        self.ble_mock.add_r_sn(17, 2300000000000)
        # DC input power
        self.ble_mock.add_r_int(36, 10)
        # AC input power
        self.ble_mock.add_r_int(37, 8)
        # AC output power
        self.ble_mock.add_r_int(38, 9)
        # AC output power
        self.ble_mock.add_r_int(39, 7)
        # SOC
        self.ble_mock.add_r_int(43, 78)

    async def test_read_all_correct(self):
        device = BaseDeviceV1()
        reader = DeviceReader(
            "00:11:00:11:00:11",
            device,
            asyncio.Future,
            ble_client=self.ble_mock,
        )

        data = await reader.read()

        self.assertEqual(data.get(FieldName.DEVICE_TYPE.value), "AC300")
        self.assertEqual(data.get(FieldName.DEVICE_SN.value), 2300000000000)
        self.assertEqual(data.get(FieldName.DC_INPUT_POWER.value), 10)
        self.assertEqual(data.get(FieldName.AC_INPUT_POWER.value), 8)
        self.assertEqual(data.get(FieldName.AC_OUTPUT_POWER.value), 9)
        self.assertEqual(data.get(FieldName.DC_OUTPUT_POWER.value), 7)
        self.assertEqual(data.get(FieldName.BATTERY_SOC.value), 78)

    async def test_read_soc_wrong(self):
        # SOC
        self.ble_mock.add_r_int(43, 1234)

        device = BaseDeviceV1()
        reader = DeviceReader(
            "00:11:00:11:00:11",
            device,
            asyncio.Future,
            ble_client=self.ble_mock,
        )

        data = await reader.read()

        self.assertIsNone(data.get(FieldName.BATTERY_SOC.value))


class TestDeviceReaderWrite(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.ble_mock = ClientMockNoEncryption()

    @patch("asyncio.sleep", return_value=None)
    async def test_write_switch_field(self, mock_sleep):
        device = BluettiDevice(
            fields=[SwitchField(FieldName.CTRL_AC, 2011)],
        )
        reader = DeviceReader(
            "00:11:00:11:00:11",
            device,
            asyncio.Future,
            ble_client=self.ble_mock,
        )

        result = await reader.write(FieldName.CTRL_AC.value, True)
        self.assertTrue(result)

    @patch("asyncio.sleep", return_value=None)
    async def test_write_number_field(self, mock_sleep):
        device = BluettiDevice(
            fields=[
                NumberField(FieldName.BATTERY_SOC_RANGE_START, 2022, min=0, max=100),
            ],
        )
        reader = DeviceReader(
            "00:11:00:11:00:11",
            device,
            asyncio.Future,
            ble_client=self.ble_mock,
        )

        result = await reader.write(FieldName.BATTERY_SOC_RANGE_START.value, 75)
        self.assertTrue(result)

    @patch("asyncio.sleep", return_value=None)
    async def test_write_non_writeable_field(self, mock_sleep):
        device = BluettiDevice(
            fields=[SwitchField(FieldName.CTRL_AC, 2011)],
        )
        reader = DeviceReader(
            "00:11:00:11:00:11",
            device,
            asyncio.Future,
            ble_client=self.ble_mock,
        )

        result = await reader.write("nonexistent_field", True)
        self.assertFalse(result)
