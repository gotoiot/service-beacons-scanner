#!/usr/bin/python
from flask import request
from flask_restful import Resource

from log import error, warn, info, debug
from ibeacon.services import *


class IBeaconStartScannerResource(Resource):

    def post(self):
        fake_scan = False
        if 'fake_scan' in request.json and isinstance(request.json['fake_scan'], bool):
            fake_scan = request.json['fake_scan']
        ibeacon_start_scanner(fake_scan=fake_scan)
        return {
            'status': 'ok'
        }


class IBeaconStopScannerResource(Resource):

    def post(self):
        ibeacon_stop_scanner()
        return {
            'status': 'ok'
        }

        
class IBeaconScannerStatusResource(Resource):

    def get(self):
        return ibeacon_get_scanner_status()

    def post(self):
        return ibeacon_set_scanner_status(**request.json)

        
class IBeaconScannerSettingsResource(Resource):

    def get(self):
        return ibeacon_get_scanner_settings()

    def post(self):
        return ibeacon_set_scanner_settings(**request.json)

        
class IBeaconScannerBeaconsResource(Resource):

    def get(self, data):
        return ibeacon_get_read_beacons_info()

        
class IBeaconScannerInfoResource(Resource):

    def get(self, data):
        return ibeacon_get_scanner_full_info()
