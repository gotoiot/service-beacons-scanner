#!/usr/bin/python
import random
import json
import time
from threading import Thread
from multiprocessing import shared_memory

from beacontools import BeaconScanner
from beacontools import IBeaconFilter

from log import error, warn, info, debug
from config import config_write, lowercase_dict_keys
from config import MIN_SCAN_TICK, MAX_SCAN_TICK, RUN_FLAG, \
    SCAN_TICK, UUID_FILTER, FAKE_SCAN, BEACONS_LIST_CAPACITY

RUN_LOOP_THREAD_NAME = "ibeacon_thread"
BEACONS_DATA_SHM = "ibeacon_data"
SCANNER_SETTINGS_SHM = "ibeacon_scanner_settings"

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
        return f"_IBeacon(" + \
            f"mac_address='{self.mac_address}', " + \
            f"uuid='{self.uuid}', " + \
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


def _shared_memory_init(**kwargs):
    if not 'name' in kwargs:
        return
    if not 'data_dict' in kwargs:
        return
    shm = shared_memory.ShareableList([json.dumps(kwargs['data_dict'])], name=kwargs['name'])
    return shm


def _shared_memory_del(**kwargs):
    if not 'name' in kwargs:
        return
    shm = shared_memory.ShareableList(**kwargs)
    shm.shm.close()
    shm.shm.unlink()


def _shared_memory_get_dict(**kwargs):
    if not 'name' in kwargs:
        return
    shm = shared_memory.ShareableList(**kwargs)
    return json.loads(shm[0])


def _shared_memory_set_dict(**kwargs):
    if not 'name' in kwargs:
        return
    if not 'data_dict' in kwargs:
        return
    shm = shared_memory.ShareableList(name=kwargs['name'])
    shm[0] = json.dumps(kwargs['data_dict'])


def _publish_event_nearest_ibeacon_changes(**kwargs):
    if not 'data' in kwargs:
        return
    info(f"Publishing event NearestiBeaconChange: {kwargs['data']}")


def _publish_event_ibeacon_read(**kwargs):
    if not 'data' in kwargs:
        return
    # info(f"Publishing event iBeaconRead: {kwargs['data']}")


def _scan_beacons(**kwargs):
    beacons_list = []
    # read beaconstools callback
    def _scans_callback(bt_addr, rssi, packet, additional_info):
        beacon = _IBeacon(bt_addr, packet.uuid, packet.major, packet.minor, packet.tx_power, rssi)
        if beacon not in beacons_list:
            beacons_list.append(beacon)
    # create and start scanner en each cycle
    beaconstools_scanner = BeaconScanner(
        _scans_callback, 
        device_filter=IBeaconFilter(uuid=kwargs['uuid_filter'])
    )
    beaconstools_scanner.start()
    time.sleep(kwargs['scan_tick'])
    beaconstools_scanner.stop()
    # return beacon_list
    return beacons_list


def _scan_beacons_fake(**kwargs):
    beacons_list = []
    beacons_list.append(_IBeacon("11:11:11", UUID_FILTER, 11, 1, -50, random.randint(1, 100) * -1))
    beacons_list.append(_IBeacon("22:22:22", UUID_FILTER, 11, 2, -50, random.randint(1, 100) * -1))
    beacons_list.append(_IBeacon("33:33:33", UUID_FILTER, 11, 3, -50, random.randint(1, 100) * -1))
    time.sleep(kwargs['scan_tick'])
    return beacons_list


def _is_nearest_beacon_changes(last_beacons_list, new_beacons_list):
    if not last_beacons_list and not new_beacons_list:
        return False
    if not last_beacons_list or not new_beacons_list:
        return True
    if last_beacons_list[0].hash() != new_beacons_list[0].hash():
        return True
    return False


def _get_last_beacon_list_from_shm():
    last_beacons_data = _shared_memory_get_dict(name=BEACONS_DATA_SHM)
    last_beacons_list = last_beacons_data["beacons_list"]
    return [_IBeacon(**beacon_data) for beacon_data in last_beacons_list] \
        if last_beacons_list else []


def _render_beacons_data(beacons_list):
    return {
        'nearest_beacon' : vars(beacons_list[0]) if beacons_list else None,
        'beacons_list' : [vars(b) for b in beacons_list] if beacons_list else [],
    }


def _run_scanner_loop():
    while 1:
        scanner_settings = _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM)
        if scanner_settings['run_flag']:
            # performs ibeacon scanning
            if scanner_settings['fake_scan']:
                current_beacons_list = _scan_beacons_fake(**scanner_settings)
            else:
                current_beacons_list = _scan_beacons(**scanner_settings)
            # accomodate data for this new cycle
            current_beacons_list = sorted(current_beacons_list)
            last_beacons_list = sorted(_get_last_beacon_list_from_shm())
            beacons_data_dict = _render_beacons_data(current_beacons_list)
            # compare new beacons list against last list and performs actions
            if _is_nearest_beacon_changes(last_beacons_list, current_beacons_list):
                debug("Nearest beacon has changed")
                nearest_beacon_data = beacons_data_dict["nearest_beacon"]
                _publish_event_nearest_ibeacon_changes(data=nearest_beacon_data)
            # updates global system beacon data
            if current_beacons_list and current_beacons_list != last_beacons_list:
                _publish_event_ibeacon_read(data=beacons_data_dict)
            _shared_memory_set_dict(name=BEACONS_DATA_SHM, data_dict=beacons_data_dict)


def ibeacon_init_scanner():
    info("Initializing iBeacon Scanner")
    scanner_settings = {
        'uuid_filter': UUID_FILTER,
        'scan_tick': SCAN_TICK,
        'run_flag': RUN_FLAG,
        'fake_scan': FAKE_SCAN,
    }
    _shared_memory_init(name=SCANNER_SETTINGS_SHM, data_dict=scanner_settings)
    initial_beacons_data = _render_beacons_data([_IBeacon("","",0,0,0,0) for _ in range(BEACONS_LIST_CAPACITY)])
    _shared_memory_init(name=BEACONS_DATA_SHM, data_dict=initial_beacons_data)
    run_thread = Thread(name=RUN_LOOP_THREAD_NAME, target=_run_scanner_loop)
    run_thread.start()


def ibeacon_start_scanner():
    info("Starting iBeacon Scanner")
    ibeacon_set_scanner_settings(run_flag=True)


def ibeacon_stop_scanner():
    info("Stopping iBeacon Scanner")
    ibeacon_set_scanner_settings(run_flag=False)


def ibeacon_get_beacons_data():
    return _shared_memory_get_dict(name=BEACONS_DATA_SHM)


def ibeacon_set_scanner_settings(**kwargs):
    kwargs = lowercase_dict_keys(kwargs)
    current_settings = _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM)

    if 'uuid_filter' in kwargs and isinstance(kwargs['uuid_filter'], str):
        current_settings["uuid_filter"] = kwargs["uuid_filter"]
        debug(f"IBeaconScanner 'uuid_filter' update to: {current_settings['uuid_filter']}")

    if 'scan_tick' in kwargs and isinstance(kwargs['scan_tick'], int):
        if kwargs["scan_tick"] < MIN_SCAN_TICK:
            current_settings["scan_tick"] = MIN_SCAN_TICK
        elif kwargs["scan_tick"] > MAX_SCAN_TICK:
            current_settings["scan_tick"] = MAX_SCAN_TICK
        else:
            current_settings["scan_tick"] = kwargs["scan_tick"]
        debug(f"IBeaconScanner 'scan_tick' update to: {current_settings['scan_tick']}")

    if 'fake_scan' in kwargs and isinstance(kwargs['fake_scan'], bool):
        current_settings["fake_scan"] = kwargs['fake_scan']
        debug(f"IBeaconScanner 'fake_scan' update to: {current_settings['fake_scan']}")

    if 'run_flag' in kwargs and isinstance(kwargs['run_flag'], bool):
        current_settings["run_flag"] = kwargs['run_flag']
        debug(f"IBeaconScanner 'run_flag' update to: {current_settings['run_flag']}")
        
    if current_settings != _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM):
        config_write(**current_settings)
        _shared_memory_set_dict(name=SCANNER_SETTINGS_SHM, data_dict=current_settings)
        info("Updated new scanner settings")


def ibeacon_get_scanner_settings():
    return _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM)
