import os
import sys
import json
import requests


ENV = os.getenv('ENV')
if not ENV:
    print("ENV not specified")
    sys.exit(1)

LOCAL_SETTINGS_FILE = os.getenv('LOCAL_SETTINGS_FILE', '/app/_service_storage/settings.json')
if not os.path.exists(LOCAL_SETTINGS_FILE):
    print("LOCAL_SETTINGS_FILE not specified")
    sys.exit(1)

LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
LOG_FORMAT = os.getenv('LOG_FORMAT', '[ %(levelname)5s ] - %(message)s')
PORT = int(os.getenv('PORT', 5000))


def _get_this_module():
    return sys.modules[__name__]


def _read_local_config():
    return json.loads(open(LOCAL_SETTINGS_FILE).read())


def _write_local_config(**kwargs):
    config_data = _read_local_config()
    for key in config_data:
        if key in kwargs:
            config_data[key] = kwargs[key]
    try:
        with open(LOCAL_SETTINGS_FILE, 'w') as config_file:
            json.dump(config_data, config_file, ensure_ascii=False, indent=4)
            print("[  INFO ] - Updated LOCAL_SETTINGS_FILE with new data")
    except:
        print("[ ERROR ] - Impossible to update LOCAL_SETTINGS_FILE")
    return config_data


def _set_module_attributes(attributes):
    attributes = uppercase_dict_keys(attributes)
    this_module = _get_this_module()
    for key, value in attributes.items():
        setattr(this_module, key, value)


def uppercase_dict_keys(base_dict):
    out_dict = {}
    for k, v in base_dict.items():
        if isinstance(v, dict):
            v = uppercase_dict_keys(v)
        out_dict[k.upper()] = v
    return out_dict


def lowercase_dict_keys(base_dict):
    out_dict = {}
    for k, v in base_dict.items():
        if isinstance(v, dict):
            v = lowercase_dict_keys(v)
        out_dict[k.lower()] = v
    return out_dict


def config_read():
    """ Manages the configuration read
    
    It works for local service storage config and event for remote config
    """
    return _read_local_config()


def config_write(**kwargs):
    """ Manages the configuration write
    
    It works for local service storage config and event for remote config
    """
    kwargs = uppercase_dict_keys(kwargs)
    new_config_data = _write_local_config(**kwargs)
    return new_config_data


def config_get_current_settings_as_list():
    settings_list = []
    config_data = config_read()
    variables_to_show = list(config_data.keys()) + [
        'ENV',
        'LOG_LEVEL',
        'LOCAL_SETTINGS_FILE',
        'PORT',
        ]
    this_module = _get_this_module()
    for key in sorted(variables_to_show):
        settings_list.append(f"{key} = {getattr(this_module, key)}")
    return settings_list


def config_synchronize():
    """ Synchronize settings between local config and remote config """
    pass

# once the module code is loaded, sets dynamic attrs
_set_module_attributes(config_read())
