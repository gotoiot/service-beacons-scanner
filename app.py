#!/usr/bin/python
import traceback

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS

import config
from log import error, warn, info, debug
from ibeacon.resources import *
from ibeacon.services import * 


##########[ Settings & Data ]##################################################


application = Flask(
    __name__,
    static_url_path='/assets',
    static_folder='static',
)
api = Api(application)
CORS(application)
application.config['PROPAGATE_EXCEPTIONS'] = True


#########[ Flask Application setup ]###########################################


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


#########[ Flask Application resources ]#######################################


api.add_resource(IBeaconStartScannerResource, '/ibeacons_scanner/start')
api.add_resource(IBeaconStopScannerResource, '/ibeacons_scanner/stop')
api.add_resource(IBeaconScannerStatusResource, '/ibeacons_scanner/status')
api.add_resource(IBeaconScannerSettingsResource, '/ibeacons_scanner/settings')
api.add_resource(IBeaconScannerBeaconsResource, '/ibeacons_scanner/beacons/<data>')
api.add_resource(IBeaconScannerInfoResource, '/ibeacons_scanner/info/<data>')


#########[ Main code ]#########################################################


def ibeacon_onchange_callback(changes_data):
    info(f"Calling changes callback with data: {changes_data}")


def init_app():
    print ("Welcome to Beacons Scanner - Powered by Goto IoT")
    ibeacon_init_scanner()
    ibeacon_set_onchange_callback(ibeacon_onchange_callback)


init_app()

if __name__ == "__main__":
    application.run(
        host="0.0.0.0", 
        port=config.PORT, 
        debug=True
        )