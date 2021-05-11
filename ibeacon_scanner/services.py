#!/usr/bin/python
import time
from threading import Thread
import json

from beacontools import BeaconScanner
from beacontools import IBeaconFilter

from log import error, warn, info, debug
from comms.http import send_http_post_request
from config import IBEACON_MIN_SCAN_TICK, IBEACON_MAX_SCAN_TICK, IBEACON_RUN_FLAG, \
    IBEACON_SCAN_TICK, IBEACON_UUID_FILTER, IBEACON_FAKE_SCAN, IBEACON_HTTP_ONCHANGE_CALLBACK_URL

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
        self._http_onchange_callback_url = kwargs.get('http_onchange_callback_url')
        self._nearest_beacon = _IBeacon()
        self._last_nearest_beacon = _IBeacon()
        self._beacons_list = []
        self._scan_thread = None
        self._run_flag = False
        self._fake_scan = kwargs.get('fake_scan', False)
        if 'run_flag' in kwargs and isinstance(kwargs['run_flag'], bool) and kwargs['run_flag']:
            self.start()

    def start(self):
        self._show_debug_data("start")
        if not self._run_flag:
            self._run_flag = True
            info(f"Starting iBeaconScanner: {self.get_scanner_settings()}")
            thread_target = self._scan
            if self._fake_scan:
                thread_target = self._scan_fake
            self._scan_thread = Thread(target=thread_target)
            self._scan_thread.start()

    def stop(self):
        self._show_debug_data("stop")
        if self._run_flag:
            self._run_flag = False
            info("Stopping IBeaconScanner")
            self._scan_thread.join(timeout=float(IBEACON_MAX_SCAN_TICK))
            info("IBeaconScanner stopped")

    def get_scanner_settings(self):
        return {
            'uuid_filter': self._uuid_filter,
            'scan_tick': self._scan_tick,
            'run_flag': self._run_flag,
            'fake_scan': self._fake_scan,
            'http_onchange_callback_url': self._http_onchange_callback_url,
        }

    def get_beacons_data(self):
        return {
            'nearest_beacon' : vars(self.nearest_beacon) if self.nearest_beacon else None,
            'last_nearest_beacon' : vars(self.last_nearest_beacon) if self.last_nearest_beacon else None,
            'beacons_list' : [vars(b) for b in self._beacons_list] if self._beacons_list else None,
        }

    def update_scanner_behaviour(self, **kwargs):
        if 'uuid_filter' in kwargs and isinstance(kwargs['uuid_filter'], str):
            self._uuid_filter = kwargs["uuid_filter"]
            debug(f"IBeaconScanner 'uuid_filter' update to: {self._uuid_filter}")

        if 'scan_tick' in kwargs and isinstance(kwargs['scan_tick'], int):
            if kwargs["scan_tick"] < IBEACON_MIN_SCAN_TICK:
                self._scan_tick = IBEACON_MIN_SCAN_TICK
            elif kwargs["scan_tick"] > IBEACON_MAX_SCAN_TICK:
                self._scan_tick = IBEACON_MAX_SCAN_TICK
            else:
                self._scan_tick = kwargs["scan_tick"]
            debug(f"IBeaconScanner 'scan_tick' update to: {self._scan_tick}")

        if 'http_onchange_callback_url' in kwargs and isinstance(kwargs['http_onchange_callback_url'], str):
            self._http_onchange_callback_url = kwargs["http_onchange_callback_url"]
            debug(f"IBeaconScanner 'http_onchange_callback_url' update to: {self._http_onchange_callback_url}")

        if 'fake_scan' in kwargs and isinstance(kwargs['fake_scan'], bool):
            self._fake_scan = kwargs['fake_scan']
            debug(f"IBeaconScanner 'fake_scan' update to: {self._fake_scan}")

        if 'run_flag' in kwargs and isinstance(kwargs['run_flag'], bool):
            self.start() if kwargs['run_flag'] else self.stop()

    def _scan(self):
        def _scans_callback(bt_addr, rssi, packet, additional_info):
            beacon = _IBeacon(bt_addr, packet.uuid, packet.major, packet.minor, packet.tx_power, rssi)
            if not beacon in self._beacons_list:
                self._beacons_list.append(beacon)
        
        while(self._run_flag):
            self._show_debug_data("_scan")
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
                info(f"Nearest beacon: {self._nearest_beacon}")
            else:
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = None
                info("No beacons found in this scan")
            if self._is_nearest_beacon_changes():
                self._invoke_onchange_callbacks()
        info(f"Finished scan_fake execution")

    def _scan_fake(self):
        import random
        while(self._run_flag):
            self._show_debug_data("_scan_fake")
            self._beacons_list.clear()
            self._beacons_list.append(_IBeacon("11:11:11", IBEACON_UUID_FILTER, 11, 1, -50, random.randint(1, 100) * -1))
            self._beacons_list.append(_IBeacon("22:22:22", IBEACON_UUID_FILTER, 11, 2, -50, random.randint(1, 100) * -1))
            self._beacons_list.append(_IBeacon("33:33:33", IBEACON_UUID_FILTER, 11, 3, -50, random.randint(1, 100) * -1))
            time.sleep(self._scan_tick)
            if self._beacons_list:
                self._beacons_list = sorted(self._beacons_list)
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = self._beacons_list[0]
                info(f"Nearest beacon: {self._nearest_beacon}")
            else:
                self._last_nearest_beacon = self._nearest_beacon
                self._nearest_beacon = None
                warn("No beacons found in this scan")
            if self._is_nearest_beacon_changes():
                self._invoke_onchange_callbacks()
        info(f"Finished scan_fake execution")

    def _show_debug_data(self, fn):
        debug(f"DEBUG_DATA - fn: {fn}, run_flag: {self._run_flag}, instance: {id(self)}, scan_thread: {self._scan_thread}")

    def _is_nearest_beacon_changes(self):
        if not self._nearest_beacon and not self._last_nearest_beacon:
            return False
        if not self._nearest_beacon or not self._last_nearest_beacon:
            return True
        if self.nearest_beacon.hash() != self.last_nearest_beacon.hash():
            return True
        return False

    def _invoke_onchange_callbacks(self):
        if self._http_onchange_callback_url:
            url = self._http_onchange_callback_url
            data = json.dumps(self.get_beacons_data())
            try:
                send_http_post_request(url=url, data=data)
                info(f"Called http callback at '{self._http_onchange_callback_url}' succesfully")
            except Exception as e:
                error(f"While calling http callback at '{self._http_onchange_callback_url}'. Error: '{e}'")

    def __repr__(self):
        return f"IBeaconScanner(" + \
            f"uuid_filter={self._uuid_filter}, " + \
            f"scan_tick={self._scan_tick}, " + \
            f"run_flag={self._run_flag}, " + \
            f"fake_scan={self._fake_scan}, " + \
            f"http_onchange_callback_url={self._http_onchange_callback_url}" + \
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
        

def _get_scanner_settings_from_config():
    return {
        'uuid_filter': IBEACON_UUID_FILTER,
        'scan_tick': IBEACON_SCAN_TICK,
        'run_flag': IBEACON_RUN_FLAG,
        'fake_scan': IBEACON_FAKE_SCAN,
        'http_onchange_callback_url': IBEACON_HTTP_ONCHANGE_CALLBACK_URL,
    }


def _get_scanner_settings_as_config_keys():
    data = _ibeacons_scanner.get_scanner_settings()
    return {
        "IBEACON_UUID_FILTER": data['uuid_filter'],
        "IBEACON_SCAN_TICK": data['scan_tick'],
        "IBEACON_RUN_FLAG": data['run_flag'],
        "IBEACON_FAKE_SCAN": data['fake_scan'],
        "IBEACON_HTTP_ONCHANGE_CALLBACK_URL": data['http_onchange_callback_url'],
    }


def _ibeacon_scanner_onchange_callback(data):
    if IBEACON_HTTP_ONCHANGE_CALLBACK_URL:
        url = IBEACON_HTTP_ONCHANGE_CALLBACK_URL
        data = json.dumps(data)
        try:
            send_http_post_request(url=url, data=data)
            info(f"Called http callback at '{url}' succesfully")
        except Exception as e:
            error(f"While calling http callback at '{url}'. Error: '{e}'")


def ibeacon_init_scanner():
    global _ibeacons_scanner
    scanner_settings = _get_scanner_settings_from_config()
    _ibeacons_scanner = _IBeaconsScanner(**scanner_settings)


def ibeacon_start_scanner():
    _ibeacons_scanner.start()


def ibeacon_stop_scanner():
    _ibeacons_scanner.stop()


def ibeacon_get_scanner_settings(config_notation=False):
    if config_notation:
        return _get_scanner_settings_as_config_keys()
    return _ibeacons_scanner.get_scanner_settings()


def ibeacon_update_scanner_behaviour(**kwargs):
    return _ibeacons_scanner.update_scanner_behaviour(**kwargs)


def ibeacon_get_beacons_data():
    return _ibeacons_scanner.get_beacons_data()

