#!/usr/bin/python
import os
import random
import json
import time
from threading import Thread
from multiprocessing import shared_memory

from beacontools import BeaconScanner
from beacontools import IBeaconFilter

from persistance import read_local_cache_file, write_local_cache_file
from event.services import publish_event
from ibeacon_scanner.models import IBeacon
from ibeacon_scanner.events import IBeaconChange, IBeaconRead
from log import error, warn, info, debug
from config import config_write, lowercase_dict_keys
from config import MIN_SCAN_TICK, MAX_SCAN_TICK, RUN_FLAG, \
    SCAN_TICK, UUID_FILTER, FAKE_SCAN, BEACONS_LIST_CAPACITY


FILEPATH_BEACONS_DATA = "/local/storage/ibeacon_data.json"
FILEPATH_SCANNER_SETTINGS = "/local/storage/ibeacon_scanner_settings.json"


def _get_last_beacon_list():
    """ Obtains the last list reading it from cache file or any other method. """
    last_beacons_data = read_local_cache_file(filepath=FILEPATH_BEACONS_DATA)
    last_beacons_list = last_beacons_data["beacons_list"]
    return [IBeacon(**beacon_data) for beacon_data in last_beacons_list] \
        if last_beacons_list else []


def _render_beacons_data(beacons_list):
    return {
        'nearest_beacon' : vars(beacons_list[0]) if beacons_list else None,
        'beacons_list' : [vars(b) for b in beacons_list] if beacons_list else [],
    }


def _scan_beacons(**kwargs):
    beacons_list = []
    # read beaconstools callback
    def _scans_callback(bt_addr, rssi, packet, additional_info):
        beacon = IBeacon(bt_addr, packet.uuid, packet.major, packet.minor, packet.tx_power, rssi)
        if beacon not in beacons_list:
            beacons_list.append(beacon)
    # create and start scanner in each cycle
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
    beacons_list.append(IBeacon("11:11:11", UUID_FILTER, 11, 1, -50, random.randint(1, 100) * -1))
    beacons_list.append(IBeacon("22:22:22", UUID_FILTER, 11, 2, -50, random.randint(1, 100) * -1))
    beacons_list.append(IBeacon("33:33:33", UUID_FILTER, 11, 3, -50, random.randint(1, 100) * -1))
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


def _run_scanner_loop():
    while 1:
        scanner_settings = read_local_cache_file(filepath=FILEPATH_SCANNER_SETTINGS)
        if scanner_settings['run_flag']:
            # performs ibeacon scanning
            if scanner_settings['fake_scan']:
                current_beacons_list = _scan_beacons_fake(**scanner_settings)
            else:
                current_beacons_list = _scan_beacons(**scanner_settings)
            # accomodate data for this new cycle
            current_beacons_list = sorted(current_beacons_list)
            last_beacons_list = sorted(_get_last_beacon_list())
            beacons_data_dict = _render_beacons_data(current_beacons_list)
            # compare new beacons list against last list and performs actions
            if _is_nearest_beacon_changes(last_beacons_list, current_beacons_list):
                debug("Nearest beacon has changed")
                nearest_beacon_data = beacons_data_dict["nearest_beacon"]
                publish_event(IBeaconChange(nearest_beacon_data))
            # updates global system beacon data
            if current_beacons_list and current_beacons_list != last_beacons_list:
                publish_event(IBeaconRead(beacons_data_dict))
            write_local_cache_file(filepath=FILEPATH_BEACONS_DATA, data_dict=beacons_data_dict)


def ibeacon_init_scanner():
    info("Initializing iBeacon Scanner")
    scanner_settings_dict = {
        'uuid_filter': UUID_FILTER,
        'scan_tick': SCAN_TICK,
        'run_flag': RUN_FLAG,
        'fake_scan': FAKE_SCAN,
    }
    write_local_cache_file(filepath=FILEPATH_SCANNER_SETTINGS, data_dict=scanner_settings_dict)
    initial_beacons_list = [IBeacon("","",0,0,0,0) for _ in range(BEACONS_LIST_CAPACITY)]
    initial_beacons_data_dict = _render_beacons_data(initial_beacons_list)
    write_local_cache_file(filepath=FILEPATH_BEACONS_DATA, data_dict=initial_beacons_data_dict)
    _run_scanner_loop()


def ibeacon_start_scanner():
    info("Starting iBeacon Scanner")
    ibeacon_set_scanner_settings(run_flag=True)


def ibeacon_stop_scanner():
    info("Stopping iBeacon Scanner")
    ibeacon_set_scanner_settings(run_flag=False)


def ibeacon_get_beacons_data():
    return read_local_cache_file(filepath=FILEPATH_BEACONS_DATA)


def ibeacon_get_scanner_settings():
    return read_local_cache_file(filepath=FILEPATH_SCANNER_SETTINGS)


def ibeacon_set_scanner_settings(**kwargs):
    kwargs = lowercase_dict_keys(kwargs)
    current_settings = read_local_cache_file(filepath=FILEPATH_SCANNER_SETTINGS)

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
        
    if current_settings != read_local_cache_file(filepath=FILEPATH_SCANNER_SETTINGS):
        config_write(**current_settings)
        write_local_cache_file(filepath=FILEPATH_SCANNER_SETTINGS, data_dict=current_settings)
        info("Updated new scanner settings")
