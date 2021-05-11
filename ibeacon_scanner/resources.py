#!/usr/bin/python
from flask import request
from flask_restful import Resource

from config import config_write
from log import error, warn, info, debug
from ibeacon_scanner.services import *


class IBeaconScannerStartResource(Resource):

    def post(self):
        ibeacon_start_scanner()
        return {
            'status': 'running'
        }


class IBeaconScannerStopResource(Resource):

    def post(self):
        ibeacon_stop_scanner()
        return {
            'status': 'stopped'
        }


class IBeaconScannerSettingsResource(Resource):

    def get(self):
        return ibeacon_get_scanner_settings()

    def put(self):
        ibeacon_set_scanner_settings(**request.json)
        config_data = ibeacon_get_scanner_settings()
        config_write(**config_data)
        return ibeacon_get_scanner_settings()

        
class IBeaconScannerBeaconsDataResource(Resource):

    def get(self):
        return ibeacon_get_beacons_data()


def ibeacon_add_http_resources_to_api(flask_restful_api, prefix=""):
    info("Adding 'ibeacon_add_http_resources' resources to application")
    prefix = f"/{prefix}" if prefix and not prefix.startswith("/") else prefix
    flask_restful_api.add_resource(IBeaconScannerStartResource, f'{prefix}/start')
    flask_restful_api.add_resource(IBeaconScannerStopResource, f'{prefix}/stop')
    flask_restful_api.add_resource(IBeaconScannerSettingsResource, f'{prefix}/settings')
    flask_restful_api.add_resource(IBeaconScannerBeaconsDataResource, f'{prefix}/beacons_data')
