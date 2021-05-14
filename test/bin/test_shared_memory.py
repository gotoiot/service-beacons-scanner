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
    

_shared_memory_init(name="beacon_data", data_dict={})

_shared_memory_set_dict(name="beacon_data", data_dict={'a':1})

_shared_memory_get_dict(name="beacon_data")

_shared_memory_del(name="beacon_data")
