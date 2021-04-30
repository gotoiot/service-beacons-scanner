import os
import sys
import json


# try to read configs from env file
PORT = os.getenv("PORT", 5000)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FORMAT = os.getenv('LOG_FORMAT', '[%(levelname)s] - [%(asctime)s] - %(message)s')
DB_CONFIG = os.getenv('DB_CONFIG', '/app/db/config.json')
# load data from stored file
stored_data = json.loads(open(DB_CONFIG).read())
# set attributes dynamically
_config_module = sys.modules[__name__]


def _set_dynamic_module_attrs(dynamic_attrs):
    for key, value in dynamic_attrs.items():
        setattr(_config_module, key, value)


def read_db_config_data():
    return json.loads(open(DB_CONFIG).read())


def write_db_config_data(**kwargs):
    config_data = read_db_config_data()
    for key in config_data:
        if key in kwargs:
            config_data[key] = kwargs[key]
    try:
        with open(DB_CONFIG, 'w') as db_config:
            json.dump(
                config_data, 
                db_config, 
                ensure_ascii=False, 
                indent=4
                )
        _set_dynamic_module_attrs(config_data)
        print("Updated DB_CONFIG with new data")
    except:
        print("Impossible to update DB_CONFIG")
    return config_data


def show_current_config():
    config_data = read_db_config_data()
    variables_to_show = list(config_data.keys()) + [
        'PORT', 
        'LOG_LEVEL', 
        'DB_CONFIG',
        ]
    for key in sorted(variables_to_show):
        print(f"{key}={getattr(_config_module, key)}")


# once the module code is loaded, sets dynamic attrs
_set_dynamic_module_attrs(read_db_config_data())
