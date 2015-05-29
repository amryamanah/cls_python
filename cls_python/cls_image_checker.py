__author__ = 'user'

import time
import logging
from threading import Thread, Timer
from .main import ClsPython, adjust_led

logger = logging.getLogger(__name__)
def image_checker():
    with ClsPython() as cls:
        stop_led = False
        # timeout = time.time() + 10
        # led_thread = Thread(target=adjust_led, args=(cls, lambda: stop_led))
        # led_thread.start()

        pl_distance = cls.get_distance("pl")
        no_pldistance = cls.get_distance("nopl")
        cls.set_led("pl", pl_distance)
        cls.set_led("nopl", no_pldistance)

        time.sleep(1)

        cls.snap_and_save("id")
        cls.snap_and_save("pl")
        cls.snap_and_save("nopl")

        cls.set_led("reset", 0)

        # stop_led = True
        # led_thread.join()

