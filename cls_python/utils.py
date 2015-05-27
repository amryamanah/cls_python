__author__ = 'Amry Fitra'

import decorator
import time
import threading
import csv
import os
import psutil
import requests
import requests.exceptions
import json
import logging

logger = logging.getLogger(__name__)

def form_dct_result(header, data):
    return dict(zip(header, data))

def write_csv_result(csv_path, header, data):
    if not os.path.exists(csv_path):
        with open(csv_path, "w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()

    with open(csv_path, "a") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writerow(data)

def retry(howmany, *exception_types, **kwargs):
    timeout = kwargs.get('timeout', 0.0) # seconds

    @decorator.decorator
    def try_it(func, *fargs, **fkwargs):
        for _ in range(howmany):
            try:
                return func(*fargs, **fkwargs)
            except exception_types or Exception:
                if timeout is not None:
                    time.sleep(timeout)
    return try_it

class PeriodicTask(object):
    def __init__(self, interval, callback, *args, **kwargs):
        self.interval = interval
        self.callback = callback
        self.daemon = True
        self.kwargs = kwargs
        self.args = args

    def run(self):
        self.callback(*self.args,**self.kwargs)
        t = threading.Timer(self.interval, self.run)
        t.daemon = self.daemon
        t.start()


def send_device_condition(main_config=None):
        logger.info("[START] Sending Device Condition via REST api")
        try:
            cpu_usage = psutil.cpu_percent()
            disk_usage = psutil.disk_usage(main_config["result_drive"]).percent
            memory_usage = psutil.virtual_memory().percent
            device_condition = {
                'device_name': u'{}'.format(main_config["device_name"]),
                'cpu_usage': cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage
            }
            r = requests.post(
                "{}/device-condition".format(main_config["cls_server_url"]),
                data=json.dumps(device_condition),
                headers={'content-type': 'application/json'},
                auth=(main_config["cls_user"], main_config["cls_pass"])
            )
            if r.status_code == 200:
                logger.info("[FINISH] Sending Device Condition via REST api")
            else:
                logger.error("[FINISH] {} Failed Sending Device Condition via REST api".format(r.status_code))
        except requests.exceptions.ConnectionError as e:
            logger.error("[ERROR] {}".format(e))


def send_device_error(main_config, level, component, error):
        logger.info("[START] Sending Device Error via REST api")
        try:
            device_error = {
                'device_name': u'{}'.format(main_config["device_name"]),
                'level': level,
                "component": component,
                "message": error
            }
            r = requests.post(
                "{}/device-error".format(main_config["cls_server_url"]),
                data=json.dumps(device_error),
                headers={'content-type': 'application/json'},
                auth=(main_config["cls_user"], main_config["cls_pass"])
            )

            if r.status_code == 200:
                logger.info("[FINISH] Sending Device Error via REST api")
            else:
                logger.error("[FINISH] {} Failed Sending Device Error via REST api".format(r.status_code))
        except requests.exceptions.ConnectionError as e:
            logger.error("[ERROR] {}".format(e))
