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

        controller.set_led("pl", pl_distance)
        controller.set_led("nopl", no_pldistance)
    logger.info("[FINISH] adjust_led thread")

def image_checker():
    with ClsPython() as cls:
        pl_timeout = time.time() + 2

        while time.time() < pl_timeout:
            pl_distance = cls.get_distance("pl")
            cls.set_led("pl", pl_distance)
            cls.snap_and_save("pl")

        cls.set_led("reset", 0)
        nopl_timeout = time.time() + 2

        while time.time() < nopl_timeout:
            no_pldistance = cls.get_distance("nopl")
            cls.set_led("nopl", no_pldistance)
            cls.snap_and_save("nopl")

        cls.snap_and_save("id")
        cls.set_led("reset", 0)

