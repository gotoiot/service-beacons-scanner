import os
import json
import time

from log import warn


def write_local_cache_file(**kwargs):
    if not 'filepath' in kwargs:
        return
    if not 'data_dict' in kwargs:
        return
    if not kwargs['data_dict']:
        kwargs['data_dict'] = {}
    cycles = 0
    while cycles < 5:
        try:
            os.makedirs(os.path.dirname(kwargs['filepath']), exist_ok=True)
            with open(kwargs['filepath'], 'w') as _file:
                json.dump(kwargs['data_dict'], _file, ensure_ascii=False, indent=4)
            return
        except:
            warn(f"While trying to write local cache file '{kwargs['filepath']}'. Retrying...")
        cycles += 1
        time.sleep(1)


def read_local_cache_file(**kwargs):
    if not 'filepath' in kwargs:
        return
    cycles = 0
    while cycles < 5:
        try:
            return json.loads(open(kwargs['filepath']).read())
        except:
            warn(f"While trying to read local cache file '{kwargs['filepath']}'. Retrying...")
        cycles += 1
        time.sleep(1)
    return {}
