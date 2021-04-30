#!/usr/bin/python
import time
from threading import Thread
import json

from beacontools import BeaconScanner
from beacontools import IBeaconFilter

from log import error, warn, info, debug


DEFAULT_SCAN_TICK      = 3	
DEFAULT_BEACONS_FILTER = "ffffffff-bbbb-cccc-dddd-eeeeeeeeeeee"
MIN_SCAN_TICK          = 1
MAX_SCAN_TICK          = 10

_ibeacons_scanner      = None


class _IBeacon:
    """ Class that represents an iBeacon packet """

    def __init__(self, mac_address="", uuid="", major=0, minor=0, tx_power=0, rssi=0):
        self.mac_address = mac_address
        self.uuid = uuid
        self.major = major
        self.minor = minor
        self.tx_power = tx_power
        self.rssi = rssi		

    def hash(self):
        return hash(
           str(self.mac_address) + 
           str(self.major) +
           str(self.minor)
        )

    def __repr__(self):
        return f"IBeacon(" + \
            f"mac_address={self.mac_address}, " + \
            f"uuid={self.uuid}, " + \
            f"major={self.major}, " + \
            f"minor={self.minor}, " + \
            f"tx_power={self.tx_power}, " + \
            f"rssi={self.rssi}" + \
        ")"

    def __eq__(self, other):
        if self.hash() == other.hash():
            return True
        return False

    def __lt__(self, other):
         return other.rssi < self.rssi


class _IBeaconsScanner:
    """ 
    This class is used to perform all beacons operations like:
        - start/stop scanner
        - set callback
        - set beacons filter and scan tick
        - get beacons info
    """

    def __init__(self, uuid_filter=DEFAULT_BEACONS_FILTER, scan_tick=DEFAULT_SCAN_TICK):
        self._beacons_list        = []
        self._uuid_filter         = uuid_filter
        self._scan_tick           = scan_tick
        self._nearest_beacon      = _IBeacon()
        self._last_nearest_beacon = self._nearest_beacon
        self._run_flag            = False
        self._scan_thread         = None
        self._onchange_callback   = None

    def start(self, fake_scan=False):
        if not self._run_flag:
            info(f"Starting iBeaconScanner: {self.get_scanner_settings()}")
            self._run_flag = True
            self._scan_thread = Thread(target=self._scan_fake if fake_scan else self._scan)
            self._scan_thread.start()

    def stop(self):
        if self._run_flag:
            self._run_flag = False
            self._scan_thread.join()
            info("Stopped iBeacons scanner")

    def set_onchange_callback(self, callback=None):
        if not callback:
            warn("Changes callback is invalid")
            return
        info("Setting changes callback")
        self._onchange_callback = callback

    def get_scanner_settings(self):
        return {
            'uuid_filter': self._uuid_filter,
            'scan_tick': self._scan_tick,
        }

    def set_scanner_settings(self, **kwargs):
        if not any(k in kwargs for k in ['uuid_filter', 'scan_tick']):
            warn(f"Invalids configs for ibeacon scanner: {kwargs}")
            return
        if 'uuid_filter' in kwargs and isinstance(kwargs['uuid_filter'], str):
            self._uuid_filter = kwargs["uuid_filter"]
            debug("Updated 'uuid_filter' for ibeacon_scanner")
        if 'scan_tick' in kwargs and isinstance(kwargs['scan_tick'], int):
            if kwargs["scan_tick"] < MIN_SCAN_TICK:
                self._scan_tick = MIN_SCAN_TICK
            elif kwargs["scan_tick"] > MAX_SCAN_TICK:
                self._scan_tick = MAX_SCAN_TICK
            else:
                self._scan_tick = kwargs["scan_tick"]
            debug("Updated 'scan_tick' for ibeacon_scanner")

    def get_scanner_status(self):
        return {
            'status': 'running' if self._run_flag else 'stopped',
        }

    def set_scanner_status(self, **kwargs):
        if 'status' in kwargs and isinstance(kwargs['status'], str):
            if kwargs['status'] == 'start':
                fake_scan = False
                if 'fake_scan' in kwargs and isinstance(kwargs['fake_scan'], bool):
                    fake_scan = kwargs['fake_scan']
                self.start(fake_scan=fake_scan)
            if kwargs['status'] == 'stop':
                self.stop()
        return self.get_scanner_status()

    def get_read_beacons_info(self):
        return {
            'nearest_beacon' : vars(self._nearest_beacon) if self._nearest_beacon else None,
            'last_nearest_beacon' : vars(self._last_nearest_beacon) if self._last_nearest_beacon else None,
            'beacons_list' : [vars(b) for b in self._beacons_list] if self._beacons_list else None,
        }

    def get_scanner_full_info(self, **kwargs):
        full_data = self.get_scanner_settings()
        full_data.update(self.get_scanner_status())
        full_data.update(self.get_read_beacons_info())
        return full_data

    def _scan(self):
        def _scans_callback(bt_addr, rssi, packet, additional_info):
            beacon = _IBeacon(bt_addr, packet.uuid, packet.major, packet.minor, packet.tx_power, rssi)
            if not beacon in self._beacons_list:
                self._beacons_list.append(beacon)
        
        while(self._run_flag):
            self._beacons_list.clear()
            beaconstools_scanner = BeaconScanner(
                _scans_callback, 
                device_filter=IBeaconFilter(uuid=self._uuid_filter)
            )
            beaconstools_scanner.start()
            time.sleep(self._scan_tick)
            beaconstools_scanner.stop()
            if self._beacons_list:
                self._beacons_list = sorted(self._beacons_list)
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = self._beacons_list[0]
                info("Nearest beacon: {}".format(self._nearest_beacon))
            else:
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = None
                info("No beacons found in this scan")
            if self._is_nearest_beacon_changes():
                self._invoke_changes_callback()

    def _scan_fake(self):
        import random

        while(self._run_flag):
            self._beacons_list.clear()
            self._beacons_list.append(_IBeacon("11:11:11", DEFAULT_BEACONS_FILTER, 11, 1, -50, random.randint(1, 100) * -1))
            self._beacons_list.append(_IBeacon("22:22:22", DEFAULT_BEACONS_FILTER, 11, 2, -50, random.randint(1, 100) * -1))
            self._beacons_list.append(_IBeacon("33:33:33", DEFAULT_BEACONS_FILTER, 11, 3, -50, random.randint(1, 100) * -1))
            time.sleep(self._scan_tick)
            if self._beacons_list:
                self._beacons_list = sorted(self._beacons_list)
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = self._beacons_list[0]
                info("Nearest beacon: {}".format(self._nearest_beacon))
            else:
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = None
                warn("No beacons found in this scan")
            if self._is_nearest_beacon_changes():
                self._invoke_changes_callback()

    def _is_nearest_beacon_changes(self):
        if not self._nearest_beacon and not self._last_nearest_beacon:
            return False
        if not self._nearest_beacon or not self._last_nearest_beacon:
            return True
        if self.nearest_beacon.hash() != self.last_nearest_beacon.hash():
            return True
        return False

    def _invoke_changes_callback(self):
        if self._onchange_callback:
            debug("Calling to changes callback")
            self._onchange_callback(vars(self._nearest_beacon))

    @property
    def nearest_beacon(self):
        return self._nearest_beacon

    @property
    def last_nearest_beacon(self):
        return self._last_nearest_beacon

    @property
    def beacons_list(self):
        return self._beacons_list
        
    def __repr__(self):
        return f"IBeaconScanner(" + \
            f"uuid_filter={self._uuid_filter}, " + \
            f"scan_tick={self._scan_tick}, " + \
            f"run_flag={self._run_flag}, " + \
            f"onchange_callback={self._onchange_callback}" + \
        ")"


def ibeacon_init_scanner(scanner_config={}, onchange_callback=None):
    global _ibeacons_scanner
    _scanner_config = {k.lower(): v for k, v in scanner_config.items() \
        if k.upper() in ['UUID_FILTER', 'SCAN_TICK']} \
            if isinstance(scanner_config, dict) else {}
    _ibeacons_scanner = _IBeaconsScanner(**_scanner_config)
    _ibeacons_scanner.set_onchange_callback(onchange_callback)


def ibeacon_start_scanner(fake_scan=False):
    _ibeacons_scanner.start(fake_scan=fake_scan)


def ibeacon_stop_scanner():
    _ibeacons_scanner.stop()


def ibeacon_get_scanner_status():
    return _ibeacons_scanner.get_scanner_status()


def ibeacon_set_scanner_status(**kwargs):
    return _ibeacons_scanner.set_scanner_status(**kwargs)


def ibeacon_set_onchange_callback(callback=None):
    _ibeacons_scanner.set_onchange_callback(callback=callback)


def ibeacon_get_scanner_settings():
    return _ibeacons_scanner.get_scanner_settings()


def ibeacon_set_scanner_settings(**kwargs):
    return _ibeacons_scanner.set_scanner_settings(**kwargs)


def ibeacon_get_read_beacons_info():
    return _ibeacons_scanner.get_read_beacons_info()


def ibeacon_get_scanner_full_info():
    return _ibeacons_scanner.get_scanner_full_info()
    