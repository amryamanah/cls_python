__author__ = 'user'

import time
import logging
from threading import Thread, Timer
from .main import ClsPython

logger = logging.getLogger(__name__)

def adjust_led(controller, stop):
    logger.info("[START] adjust_led thread")
    while True:
        if stop():
            controller.set_led("reset", 0)
            break
        pl_distance = controller.get_distance("pl")
        no_pldistance = controller.get_distance("nopl")

        print("dist = {} ".format(no_pldistance))

        controller.set_led("pl", pl_distance)
        controller.set_led("nopl", no_pldistance)
    logger.info("[FINISH] adjust_led thread")

def image_checker():
    with ClsPython() as cls:
        stop_led = False
        timeout = time.time() + 10
        led_thread = Thread(target=adjust_led, args=(cls, lambda: stop_led))
        led_thread.start()

        while time.time() < timeout:
            cls.snap_and_save("pl")
            cls.snap_and_save("nopl")
        stop_led = True
        led_thread.join()




