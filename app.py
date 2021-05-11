#!/usr/bin/python
import traceback

from flask import Flask, jsonify
from flask_restful import Api
from flask_gzip import Gzip

from config import PORT, ENV, config_print_current_settings
from log import error, warn, info, debug
from ibeacon_scanner.resources import ibeacon_add_http_resources_to_api
from ibeacon_scanner.services import ibeacon_init_scanner, ibeacon_stop_scanner


application = Flask(
    __name__,
    static_url_path='/assets',
    static_folder='static',
)
flask_restful_api = Api(application)
flask_gzip = Gzip(application)
application.config['PROPAGATE_EXCEPTIONS'] = True


@application.teardown_request
def shutdown_bluetooth(_):
    ibeacon_stop_scanner()


@application.errorhandler(404)
def page_not_found(error_msg):
    response = {
        "message": str(error_msg),
    }
    return jsonify(response), 404


@application.errorhandler(Exception)
def handle_exception(error_msg):
    response = {
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
        "service_name": "ble-service",
        "status": "running",
        "env": ENV,
    })


def _get_welcome_message():
    return """\n\n
          /$$$$$$            /$$                    /$$$$$$      /$$$$$$$$
         /$$__  $$          | $$                   |_  $$_/     |__  $$__/
        | $$  \__/ /$$$$$$ /$$$$$$   /$$$$$$         | $$   /$$$$$$| $$   
        | $$ /$$$$/$$__  $|_  $$_/  /$$__  $$        | $$  /$$__  $| $$   
        | $$|_  $| $$  \ $$ | $$   | $$  \ $$        | $$ | $$  \ $| $$   
        | $$  \ $| $$  | $$ | $$ /$| $$  | $$        | $$ | $$  | $| $$   
        |  $$$$$$|  $$$$$$/ |  $$$$|  $$$$$$/       /$$$$$|  $$$$$$| $$   
         \______/ \______/   \___/  \______/       |______/\______/|__/   


                   ╔╗  ╦  ╔═╗  ╔═  ╔══ ╦═╗ ╦  ╦ ╦ ╔══ ╔═╗
                   ╠╩╗ ║  ║╣   ╚═╗ ║╣  ╠╦╝ ╚╗╔╚ ║ ║   ║╣ 
                   ╚═╝ ╩═ ╚═╝  ╚═╝ ╚══ ╩╚═  ╚╝  ╩ ╚══ ╚═╝
    \n"""


def _init_application():
    print(_get_welcome_message())
    config_print_current_settings()
    info("Starting to run BLE Service")
    ibeacon_add_http_resources_to_api(flask_restful_api, prefix="/ibeacon_scanner")
    ibeacon_init_scanner()


_init_application()


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=PORT, debug=True)