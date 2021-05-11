#!/usr/bin/python
import time
from threading import Thread

from beacontools import BeaconScanner
from beacontools import IBeaconFilter

from log import error, warn, info, debug
from config import MIN_SCAN_TICK, MAX_SCAN_TICK, RUN_FLAG, \
    SCAN_TICK, UUID_FILTER, FAKE_SCAN

_ibeacons_scanner = None


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

    def __init__(self, **kwargs):
        self._uuid_filter = kwargs.get('uuid_filter', '')
        self._scan_tick = kwargs.get('scan_tick', 5)
        self._onchange_callback = None
        self._nearest_beacon = _IBeacon()
        self._last_nearest_beacon = _IBeacon()
        self._beacons_list = []
        self._scan_thread = None
        self._run_flag = False
        self._fake_scan = kwargs.get('fake_scan', False)
        if 'run_flag' in kwargs and isinstance(kwargs['run_flag'], bool) and kwargs['run_flag']:
            self.start()

    def __repr__(self):
        return f"IBeaconScanner(" + \
            f"uuid_filter={self._uuid_filter}, " + \
            f"scan_tick={self._scan_tick}, " + \
            f"run_flag={self._run_flag}, " + \
            f"fake_scan={self._fake_scan}" + \
        ")"

    @property
    def nearest_beacon(self):
        return self._nearest_beacon

    @property
    def last_nearest_beacon(self):
        return self._last_nearest_beacon

    @property
    def beacons_list(self):
        return self._beacons_list

    def start(self):
        if not self._run_flag:
            self._run_flag = True
            info(f"Starting iBeaconScanner: {self.get_scanner_settings()}")
            thread_target = self._scan
            if self._fake_scan:
                thread_target = self._scan_fake
            self._scan_thread = Thread(target=thread_target)
            self._scan_thread.start()

    def stop(self):
        if self._run_flag:
            self._run_flag = False
            info("Waiting for scan thread finalizes iBeacon reads")
            self._scan_thread.join(timeout=float(MAX_SCAN_TICK))
            info("IBeaconScanner stopped")

    def get_beacons_data(self):
        return {
            'nearest_beacon' : vars(self.nearest_beacon) if self.nearest_beacon else None,
            'last_nearest_beacon' : vars(self.last_nearest_beacon) if self.last_nearest_beacon else None,
            'beacons_list' : [vars(b) for b in self._beacons_list] if self._beacons_list else None,
        }

    def get_scanner_settings(self):
        return {
            'uuid_filter': self._uuid_filter,
            'scan_tick': self._scan_tick,
            'run_flag': self._run_flag,
            'fake_scan': self._fake_scan,
        }

    def set_scanner_settings(self, **kwargs):
        if 'uuid_filter' in kwargs and isinstance(kwargs['uuid_filter'], str):
            self._uuid_filter = kwargs["uuid_filter"]
            debug(f"IBeaconScanner 'uuid_filter' update to: {self._uuid_filter}")

        if 'scan_tick' in kwargs and isinstance(kwargs['scan_tick'], int):
            if kwargs["scan_tick"] < MIN_SCAN_TICK:
                self._scan_tick = MIN_SCAN_TICK
            elif kwargs["scan_tick"] > MAX_SCAN_TICK:
                self._scan_tick = MAX_SCAN_TICK
            else:
                self._scan_tick = kwargs["scan_tick"]
            debug(f"IBeaconScanner 'scan_tick' update to: {self._scan_tick}")

        if 'fake_scan' in kwargs and isinstance(kwargs['fake_scan'], bool):
            self._fake_scan = kwargs['fake_scan']
            debug(f"IBeaconScanner 'fake_scan' update to: {self._fake_scan}")

        if 'run_flag' in kwargs and isinstance(kwargs['run_flag'], bool):
            self.start() if kwargs['run_flag'] else self.stop()

    def set_onchange_callback(self, callback=None):
        if not callback:
            return
        info("Setting onchange callback")
        self._onchange_callback = callback

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
            self._updates_beacons_data()
            if self._is_nearest_beacon_changes():
                self._invoke_onchange_callbacks()
        info(f"Finished _scan execution")

    def _scan_fake(self):
        import random
        while(self._run_flag):
            self._beacons_list.clear()
            self._beacons_list.append(_IBeacon("11:11:11", UUID_FILTER, 11, 1, -50, random.randint(1, 100) * -1))
            self._beacons_list.append(_IBeacon("22:22:22", UUID_FILTER, 11, 2, -50, random.randint(1, 100) * -1))
            self._beacons_list.append(_IBeacon("33:33:33", UUID_FILTER, 11, 3, -50, random.randint(1, 100) * -1))
            time.sleep(self._scan_tick)
            self._updates_beacons_data()
            if self._is_nearest_beacon_changes():
                self._invoke_onchange_callbacks()
        info(f"Finished scan_fake execution")

    def _updates_beacons_data(self):
        if self._beacons_list:
            self._beacons_list = sorted(self._beacons_list)
            self._last_nearest_beacon = self._nearest_beacon
            self._nearest_beacon = self._beacons_list[0]
            info(f"Nearest beacon: {self._nearest_beacon}")
        else:
            self._last_nearest_beacon = self._nearest_beacon
            self._nearest_beacon = None
            warn("No beacons found in this scan")

    def _is_nearest_beacon_changes(self):
        if not self._nearest_beacon and not self._last_nearest_beacon:
            return False
        if not self._nearest_beacon or not self._last_nearest_beacon:
            return True
        if self.nearest_beacon.hash() != self.last_nearest_beacon.hash():
            return True
        return False

    def _invoke_onchange_callbacks(self):
        if self._onchange_callback:
            self._onchange_callback(self.get_beacons_data())
            info(f"Called scanner onchange callback")


def ibeacon_init_scanner():
    info("Initializing iBeacon Scanner")
    global _ibeacons_scanner
    scanner_settings = {
        'uuid_filter': UUID_FILTER,
        'scan_tick': SCAN_TICK,
        'run_flag': RUN_FLAG,
        'fake_scan': FAKE_SCAN,
    }
    _ibeacons_scanner = _IBeaconsScanner(**scanner_settings)


def ibeacon_start_scanner():
    _ibeacons_scanner.start()


def ibeacon_stop_scanner():
    _ibeacons_scanner.stop()


def ibeacon_set_onchange_callback(callback):
    _ibeacons_scanner.set_onchange_callback(callback)


def ibeacon_get_scanner_settings():
    return _ibeacons_scanner.get_scanner_settings()


def ibeacon_set_scanner_settings(**kwargs):
    return _ibeacons_scanner.set_scanner_settings(**kwargs)


def ibeacon_get_beacons_data():
    return _ibeacons_scanner.get_beacons_data()

