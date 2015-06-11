__author__ = 'user'

import time
import logging
from threading import Thread, Timer
from .main import ClsPython

logger = logging.getLogger(__name__)

def image_checker():
    with ClsPython() as cls:
        pl_timeout = time.time() + 2

        while time.time() < pl_timeout:
            cls.snap_and_save("pl")

        cls.set_led("reset", 0)
        nopl_timeout = time.time() + 2

        while time.time() < nopl_timeout:
            no_pldistance = cls.get_distance("nopl")
            cls.set_led("nopl", no_pldistance)
            cls.snap_and_save("nopl")

        cls.snap_and_save("id")
        cls.set_led("reset", 0)

