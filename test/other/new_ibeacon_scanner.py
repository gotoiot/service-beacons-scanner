#!/usr/bin/python
import json
import time
from threading import Thread
from multiprocessing import shared_memory

from beacontools import BeaconScanner
from beacontools import IBeaconFilter

from log import error, warn, info, debug
from config import config_write, lowercase_dict_keys
from config import MIN_SCAN_TICK, MAX_SCAN_TICK, RUN_FLAG, \
    SCAN_TICK, UUID_FILTER, FAKE_SCAN

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


def _onchange_callback():
    # publicar un evento que ha cambiado el nearest beacon
    pass


def _onread_callback():
    # publicar un evento con la lista de beacons leidos ordenados por RSSI
    pass


def _onscan_callback():
    # lee desde beacons tools y actualiza la info en cache
    pass


def _run_scanner_loop():
    while 1:
        scanner_settings = _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM)
        debug(f"Current scanner settings are: {scanner_settings}")
        time.sleep(scanner_settings['scan_tick'])
    # leer los settings de memoria cache/compartida
    # evaluar si hay que hacer o no scan
    # evaluar si es scan fake o no
    # actualizar la memoria cache con los beacons leidos
    pass


def ibeacon_init_scanner():
    scanner_settings = {
        'uuid_filter': UUID_FILTER,
        'scan_tick': SCAN_TICK,
        'run_flag': RUN_FLAG,
        'fake_scan': FAKE_SCAN,
    }
    _shared_memory_init(name=SCANNER_SETTINGS_SHM, data_dict=scanner_settings)
    _shared_memory_init(name=BEACONS_DATA_SHM, data_dict={})
    run_thread = Thread(name=RUN_LOOP_THREAD_NAME, target=_run_scanner_loop)
    run_thread.start()


def ibeacon_start_scanner():
    # aca solamente habria que poner el run flag en false
    pass


def ibeacon_stop_scanner():
    # aca solamente habria que poner el run flag en false
    pass


def ibeacon_get_beacons_data():
    # leer el estado de la cache
    pass


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
        
    # check if config really changes
    if current_settings != _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM):
        config_write(**current_settings)
        _shared_memory_set_dict(name=SCANNER_SETTINGS_SHM, data_dict=current_settings)
        info("Updated new scanner settings")


def ibeacon_get_scanner_settings():
    return _shared_memory_get_dict(name=SCANNER_SETTINGS_SHM)
