import os
import sys
import json


PORT = os.getenv("PORT", 5000)
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FORMAT = os.getenv('LOG_FORMAT', '[%(levelname)s] - %(message)s')
CONFIG_FILEPATH = os.getenv('CONFIG_FILEPATH', '/app/db/config.json')


def _get_this_module():
    return sys.modules[__name__]


def _set_dynamic_module_attrs(dynamic_attrs):
    for key, value in dynamic_attrs.items():
        setattr(_get_this_module(), key, value)


def read_config_file():
    return json.loads(open(CONFIG_FILEPATH).read())


def write_config_file(**kwargs):
    config_data = read_config_file()
    for key in config_data:
        if key in kwargs:
            config_data[key] = kwargs[key]
    try:
        with open(CONFIG_FILEPATH, 'w') as config_file:
            json.dump(config_data, config_file, ensure_ascii=False, indent=4)
            _set_dynamic_module_attrs(config_data)
            print("Updated CONFIG_FILE with new data")
    except:
        print("Impossible to update CONFIG_FILE")
    return config_data


def show_current_config():
    config_data = read_config_file()
    variables_to_show = list(config_data.keys()) + [
        'PORT', 
        'LOG_LEVEL', 
        'DB_CONFIG',
        ]
    for key in sorted(variables_to_show):
        print(f"{key}={getattr(_get_this_module(), key)}")


# once the module code is loaded, sets dynamic attrs
_set_dynamic_module_attrs(read_config_file())
