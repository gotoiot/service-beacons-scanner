#!/usr/bin/python
from flask import request
from flask_restful import Resource

from config import write_config_file
from log import error, warn, info, debug
from ibeacon.services import *


class IBeaconScannerStartResource(Resource):

    def post(self):
        ibeacon_start_scanner()
        return {
            'status': 'ok'
        }


class IBeaconScannerStopResource(Resource):

    def post(self):
        ibeacon_stop_scanner()
        return {
            'status': 'ok'
        }


class IBeaconScannerSettingsResource(Resource):

    def get(self):
        return ibeacon_get_scanner_settings()

    def post(self):
        ibeacon_update_scanner_behaviour(**request.json)
        config_data = ibeacon_get_scanner_settings(config_notation=True)
        write_config_file(**config_data)
        return ibeacon_get_scanner_settings()

        
class IBeaconScannerBeaconsDataResource(Resource):

    def get(self):
        return ibeacon_get_beacons_data()

