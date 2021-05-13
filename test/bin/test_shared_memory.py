import json
from multiprocessing import shared_memory

data = {
    'nearest_beacon': {
        "mac":"33",
        "rssi": -51,
        "tx": 50.5,
    },
    'last_nearest_baecon': {
        "mac":"33",
        "rssi": -51,
        "tx": 50.5,
    },
    "beacons_list": [
        {
            "mac":"33",
            "rssi": -51,
            "tx": 50.5,
        },
        {
            "mac":"33",
            "rssi": -51,
            "tx": 50.5,
        },
    ]
}

data_str = json.dumps(data)
shm_a = shared_memory.ShareableList([data_str], name="beacons")

shm_b = shared_memory.ShareableList(name="beacons")
data_dict = json.loads(shm_b[0])
data_dict

data_dict['nearest_beacon']['mac'] = "66:33"
shm_b[0] = json.dumps(data_dict)
shm_a[0]

shm_b.shm.close()   
shm_a.shm.close()
shm_a.shm.unlink()


def _init_shared_memory(**kwargs):
    if not 'name' in kwargs:
        return
    if not 'data_dict' in kwargs:
        return
    shm = shared_memory.ShareableList([json.dumps(kwargs['data_dict'])], name=kwargs['name'])
    return shm


def _del_shared_memory(**kwargs):
    if not 'name' in kwargs:
        return
    shm = shared_memory.ShareableList(**kwargs)
    shm.shm.close()
    shm.shm.unlink()


def _get_shared_memory_dict(**kwargs):
    if not 'name' in kwargs:
        return
    shm = shared_memory.ShareableList(**kwargs)
    return json.loads(shm[0])


def _set_shared_memory_dict(**kwargs):
    if not 'name' in kwargs:
        return
    if not 'data_dict' in kwargs:
        return
    shm = shared_memory.ShareableList(name=kwargs['name'])
    shm[0] = json.dumps(kwargs['data_dict'])
    

_init_shared_memory(name="beacon_data", data_dict={})

_set_shared_memory_dict(name="beacon_data", data_dict={'a':1})

_get_shared_memory_dict(name="beacon_data")

_del_shared_memory(name="beacon_data")
