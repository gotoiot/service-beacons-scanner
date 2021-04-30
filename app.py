#!/usr/bin/python
import traceback

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

import config
from log import error, warn, info, debug
from ibeacon.resources import *
from ibeacon.services import * 


application = Flask(
    __name__,
    static_url_path='/assets',
    static_folder='static',
)
api = Api(application)
CORS(application)
application.config['PROPAGATE_EXCEPTIONS'] = True


@application.teardown_request
def shutdown_bluetooth(_):
    ibeacon_stop_scanner()


@application.errorhandler(404)
def page_not_found(error_msg):
    error(f"PAGE NOT FOUND: {error_msg}")
    response = {
        "error": "PAGE_NOT_FOUND",
        "message": str(error_msg),
    }
    return jsonify(response), 404


@application.errorhandler(Exception)
def handle_exception(error_msg):
    error(f"PAGE NOT FOUND: {error_msg}")
    response = {
        "error": "BAD_REQUEST",
        "message": str(error_msg),
    }
    return jsonify(response), 400


@application.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    response.headers.add('Cache-Control', 'no-store, no-cache')
    return response


@application.route("/status", methods=['GET'])
def status():
    return jsonify({
        "status": "running"
    })


def _add_application_resources():
    info("Adding resources to application")
    api.add_resource(IBeaconScannerStartResource, '/ibeacon_scanner/start')
    api.add_resource(IBeaconScannerStopResource, '/ibeacon_scanner/stop')
    api.add_resource(IBeaconScannerSettingsResource, '/ibeacon_scanner/settings')
    api.add_resource(IBeaconScannerBeaconsDataResource, '/ibeacon_scanner/beacons_data')


def init_application():
    info("Welcome to BLE Service - Powered by Goto IoT")
    _add_application_resources()
    ibeacon_init_scanner()


init_application()

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=config.PORT, debug=True)