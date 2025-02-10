""" trionesControl.py (https://github.com/Aritzherrero4/python-trionesControl)
    Pippim modifications for HomA:
    2025-01-07 SyntaxError commented out and replaced
    2025-01-10 Add hci_device="hci0" default that can be changed by caller
"""

from __future__ import print_function

import pygatt
import logging
import pygatt.exceptions 

#print("\n trionesControl.py - pygatt", pygatt.exceptions.__file__)
#trionesControl.py - pygatt /home/rick/HomA/pygatt/exceptions.pyc

MAIN_CHARACTERISTIC_UUID = "0000ffd9-0000-1000-8000-00805f9b34fb"

log = logging.getLogger(__name__)


def connect(MAC, hci_device="hci0", reset_on_start=True):
    """
    Create and start a new backend adapter and connect it to a device.

    When connecting to multiple devices at the same time make sure to set reset_on_start
    to False after the first connection is made, otherwise all connections made before are
    invalidated.

    :param string MAC: MAC address of the device to connect to.
    :param string hci_device: Added 2025-01-10 was defaulting to "hci0".
    :param bool reset_on_start: Perhaps due to a bug in gatttool or pygatt,
        but if the bluez backend isn't restarted, it can sometimes lock up
        the computer when trying to make a connection to HCI device.
    """
    adapter = pygatt.GATTToolBackend(hci_device=hci_device)  # Create instance
    try:
        adapter.start(reset_on_start=reset_on_start)
        try:
            device = adapter.connect(MAC)
        except pygatt.exceptions.NotConnectedError:
            raise pygatt.exceptions.NotConnectedError(
                "Device MAC: '" + MAC + "' not connected!")
    except pygatt.exceptions.NotConnectedError:
        raise pygatt.exceptions.NotConnectedError(
            "Adapter on device: '" + hci_device + "' cannot start!")

    ''' ORIGINAL CODE: 
    try:
        adapter = pygatt.GATTToolBackend()
        adapter.start(reset_on_start=reset_on_start)
        device = adapter.connect(MAC)
    except pygatt.exceptions.NotConnectedError:
        raise pygatt.exceptions.NotConnectedError("Device nor connected!")
    '''

    log.info("Device connected")
    return device


def disconnect(device):
    """ Disconnect Bluetooth """
    try:
        device.disconnect()
    except pygatt.exceptions.NotConnectedError:
        raise pygatt.exceptions.NotConnectedError("Device not connected!")
    log.info("Device disconnected")


def powerOn(device, wait_for_response=False):
    """
    :param device:
    :param bool wait_for_response: wait for response after writing. A GATT "command"
    is used when not waiting for a response. The remote host will not
    acknowledge the write.
    """

    try:
        device.char_write(MAIN_CHARACTERISTIC_UUID, b'\xcc\x23\x33', wait_for_response=wait_for_response)
    except pygatt.exceptions.NotConnectedError:
        raise pygatt.exceptions.NotConnectedError("Device not connected!")
    log.info("Device powered on")


def powerOff(device, wait_for_response=False):
    """
    :param device:
    :param bool wait_for_response: wait for response after writing. A GATT "command"
    is used when not waiting for a response. The remote host will not
    acknowledge the write.
    """

    try:
        device.char_write(MAIN_CHARACTERISTIC_UUID, b'\xcc\x24\x33', wait_for_response=wait_for_response)
    except pygatt.exceptions.NotConnectedError:
        raise pygatt.exceptions.NotConnectedError("Device not connected!")
    log.info("Device powered off")


# Suppress pycharm: Expected type 'int' (matched generic type '_T'), got 'str' instead
# noinspection PyTypeChecker
def setRGB(r, g, b, device, wait_for_response=False):
    """
    :param integer r: red
    :param integer g: green
    :param integer b: blue
    :param device: instance
    :param bool wait_for_response: wait for response after writing. A GATT "command"
    is used when not waiting for a response. The remote host will not
    acknowledge the write.

    2025-01-10 - HappyLighting-py
https://github.com/MikeCoder96/HappyLighting-py/blob/master/LEDStripController/BLEClass.py

    async def writeColor(self, R=0, G=0, B=0):
            lista = [86, R, G, B, (int(10 * 255 / 100) & 0xFF), 256-16, 256-86]
            values = bytearray(lista)
            try:
                Utils.printLog("Change Color called R:{} G:{} B:{} ".format(R, G, B))
                await self.client.write_gatt_char(UART_TX_CHAR_UUID, values, False)
            except Exception as inst:
                print(inst)

    async def writePower(self, state):
            lista = [204, 35, 51]
            if state == "Off":
                lista = [204, 36, 51]

            values = bytearray(lista)
            try:
                Utils.printLog("Change Power called Power : {}".format(state))
                await self.client.write_gatt_char(UART_TX_CHAR_UUID, values, False)
            except Exception as inst:
                print(inst)

    """
    # 2025-01-07 SyntaxError commented out and replaced above.
    #def setRGB(r: int, g: int, b: int, device, wait_for_response=False):
    #            ^
    # SyntaxError: invalid syntax

    # Values for color should be between 0 and 255
    #if r > 255: r = 255
    #if r < 0: r= 0
    #if g > 255: g = 255
    #if g < 0: g = 0
    #if b > 255: b = 255
    #f b < 0: b = 0
    r = 255 if r > 255 else r
    r = 0 if r < 0 else r
    g = 255 if g > 255 else g
    g = 0 if g < 0 else g
    b = 255 if b > 255 else b
    b = 0 if b < 0 else b

    payload = bytearray() 
    payload.append(0x56)

    # BELOW 3: Expected type 'int' (matched generic type '_T'), got 'str' instead
    # Python 3 error: TypeError: an integer is required
    try:
        payload.append(chr(r))
        payload.append(chr(g))
        payload.append(chr(b))
    except TypeError:
        payload.append(r)  # Original trionesControl.py code
        payload.append(g)
        payload.append(b)

    payload.append(int(10 * 255 / 100) & 0xFF)  # from HappyLighting-py
    payload.append(0xF0)
    payload.append(0xAA)
    try:
        device.char_write(MAIN_CHARACTERISTIC_UUID, payload, wait_for_response=wait_for_response)
    except (pygatt.exceptions.NotConnectedError, pygatt.exceptions.NotificationTimeout):
        raise pygatt.exceptions.NotConnectedError("Device not connected!")
    log.info("RGB set -- R: %d, G: %d, B: %d", r, g, b)


def setWhite(intensity, device, wait_for_response=False):
    #def setWhite(intensity: int, device, wait_for_response=False):
    """
    :param integer intensity:
    :param device:
    :param bool wait_for_response: wait for response after writing. A GATT "command"
    is used when not waiting for a response. The remote host will not
    acknowledge the write.
    """
    # Intensity value should be between 0  and 255
    #if (intensity > 255): intensity = 255
    #if (intensity < 0): intensity = 0
    intensity = 255 if intensity > 255 else intensity
    intensity = 0 if intensity < 0 else intensity
    payload = bytearray()
    payload.append(0x56)
    payload.append(0x0)
    payload.append(0x0)
    payload.append(0x0)
    payload.append(intensity)
    payload.append(0x0F)
    payload.append(0xAA)
    try:
        device.char_write(MAIN_CHARACTERISTIC_UUID, payload, wait_for_response=wait_for_response)
    except (pygatt.exceptions.NotConnectedError, pygatt.exceptions.NotificationTimeout):
        raise pygatt.exceptions.NotConnectedError("Device not connected!")
    log.info("White color set -- Intensity: %d", intensity)


def setBuiltIn(mode, speed, device, wait_for_response=False):
    """
    :param integer mode:
    :param integer speed:
    :param device: instance
    :param bool wait_for_response: wait for response after writing. A GATT "command"
    is used when not waiting for a response. The remote host will not
    acknowledge the write.
    """
    # def setBuiltIn(mode: int, speed: int, device, wait_for_response=False):

    if mode < 37 | mode > 56:
        raise pygatt.exceptions.BLEError("Invalid Mode")
    #if speed<1: speed =1
    #if speed > 255: speed = 255
    speed = 1 if speed < 1 else speed
    speed = 255 if speed > 255 else speed
    payload = bytearray()
    payload.append(0xBB)
    payload.append(mode)
    payload.append(speed)
    payload.append(0x44)
    try:
        device.char_write(MAIN_CHARACTERISTIC_UUID, payload, wait_for_response=wait_for_response)
    except pygatt.exceptions.NotConnectedError:
        raise pygatt.exceptions.NotConnectedError("Device not connected!")
    log.info("Default mode %d set -- Speed %d", mode, speed)
