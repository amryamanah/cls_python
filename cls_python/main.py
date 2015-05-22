import logging
import os
import time
from datetime import datetime

import addapy
import icpy3

from .config_loader import ClsConfig
from .utils import PeriodicTask

from IPython import embed


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("cls_python")

class ClsPython(object):
    def __init__(self):
        self.ic = icpy3.IC_ImagingControl()
        self.adda = addapy
        self.cls_config = ClsConfig(os.getcwd())
        self.id_cam = None
        self.pl_cam = None
        self.nopl_cam = None
        self.startup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def startup(self):
        self.ic.init_library()
        self.adda.Initialize_adda()
        self.adda.set_usb("on")
        self.setup_camera()

    def cleanup(self):
        self.ic.close_library()
        self.adda.Destroy_adda()
        self.adda.set_usb("off")

    def setup_camera(self):
        self.id_cam = self.ic.get_device_by_file(self.cls_config.get_id_cam_config_path())
        self.pl_cam = self.ic.get_device_by_file(self.cls_config.pl_cam_config_path)
        self.nopl_cam = self.ic.get_device_by_file(self.cls_config.nopl_cam_config_path)

        self.id_cam.start_live()
        self.pl_cam.start_live()
        self.nopl_cam.start_live()

    def stop_camera(self):
        self.id_cam.stop_live()
        self.pl_cam.stop_live()
        self.nopl_cam.stop_live()

    def get_last_result_folder(self):
        result_dir = self.get_or_create_result_dir()
        dir_list = os.listdir(result_dir)
        if len(dir_list) > 0:
            return int(dir_list.pop())
        else:
            return 0

    def get_or_create_result_dir(self, dir_count=""):
        a = datetime.now()
        cond = self.cls_config.get_day_period()
        print(cond)
        print(self.cls_config.MAIN["result_dir"])
        result_dir = os.path.join(self.cls_config.MAIN["result_dir"], str(a.year), str(a.month),
                                  str(a.day), cond, str(dir_count))
        os.makedirs(result_dir, exist_ok=True)
        return result_dir

    def snap_and_save(self, cam_type, result_dir):
        if cam_type == "id":
            cam = self.id_cam
            prefix = self.cls_config.ID["image_prefix"]
        elif cam_type == "pl":
            cam = self.pl_cam
            prefix = self.cls_config.PL["image_prefix"]
        elif cam_type == "nopl":
            cam = self.nopl_cam
            prefix = self.cls_config.NOPL["image_prefix"]

        try:
            picture_time = datetime.now()

            filename = "{}_{}_{}_{}_{}_{}_{}_{}.bmp".format(prefix,
                                                            picture_time.year,
                                                            picture_time.month,
                                                            picture_time.day,
                                                            picture_time.hour,
                                                            picture_time.minute,
                                                            picture_time.second,
                                                            picture_time.microsecond)
            img_path = os.path.join(result_dir, filename)
            cam.snap_image(1000)
            cam.save_image(img_path, 0)
        except icpy3.IC_Exception as e:
            logger.critical(e.message)

    def get_distance(self, type):
        if type == "pl":
            const_a = self.cls_config.PL.getfloat("distance_const_a")
            const_b = self.cls_config.PL.getfloat("distance_const_b")
            const_c = self.cls_config.PL.getfloat("distance_const_c")
        elif type == "nopl":
            const_a = self.cls_config.NOPL.getfloat("distance_const_a")
            const_b = self.cls_config.NOPL.getfloat("distance_const_b")
            const_c = self.cls_config.NOPL.getfloat("distance_const_c")

        return self.adda.get_distance(type, const_a, const_b, const_c)

    def get_temperature(self):
        return self.adda.get_temperature(self.cls_config.TEMPERATURE.getfloat("temp_const_a"),
                                         self.cls_config.TEMPERATURE.getfloat("temp_const_b"))

    def get_humidity(self):
        return self.adda.get_humidity(self.cls_config.HUMIDITY.getfloat("hum_const_a"),
                                      self.cls_config.HUMIDITY.getfloat("hum_const_b"))

    def get_illumination(self):
        return self.adda.get_illumination(self.cls_config.ILLUMINATION.getfloat("illumi_const_a"),
                                          self.cls_config.ILLUMINATION.getfloat("illumi_const_b"),
                                          self.cls_config.ILLUMINATION.getfloat("illumi_const_c"),
                                          self.cls_config.ILLUMINATION.getfloat("illumi_const_d"))

    def set_led(self, type, distance):
        if type == "pl":
            const_a = self.cls_config.PL.getfloat("led_const_a")
            const_b = self.cls_config.PL.getfloat("led_const_b")
            const_c = self.cls_config.PL.getfloat("led_const_c")
        elif type == "nopl":
            const_a = self.cls_config.NOPL.getfloat("led_const_a")
            const_b = self.cls_config.NOPL.getfloat("led_const_b")
            const_c = self.cls_config.NOPL.getfloat("led_const_c")
        elif type == "reset":
            return self.adda.set_led(type, distance, 0, 0, 0)

        return self.adda.set_led(type, distance, const_a, const_b, const_c)

    def head_check(self):
        pl_distance = self.get_distance("pl")
        nopl_distance = self.get_distance("nopl")
        cameragap = self.cls_config.MAIN.getfloat("cameragap")
        head_width = self.cls_config.MAIN.getfloat("headwidth")

        if (cameragap - pl_distance) > head_width and nopl_distance > 0:
            return True
        else:
            return False

    def drinking_check(self):  # todo check the drinking algorithm
        # todo check the drinking algorithm
        """
            check drinking
        """
        flowmeter_threshold = self.cls_config.MAIN.getint("flowmeter_threshold")
        short_sensorcount = self.adda.get_waterflow_signal()

        if short_sensorcount > flowmeter_threshold:
            return 1, short_sensorcount
        else:
            return 0, short_sensorcount

    def camera_session(self, img_folder):
        nopl_count = 0
        pl_count = 0
        id_count = 0
        timeout = time.time() + 10
        logger.info("[START] camera session")
        while time.time() < timeout:
            pl_distance = self.get_distance("pl")
            no_pldistance = self.get_distance("nopl")
            self.set_led("pl", pl_distance)
            self.set_led("nopl", no_pldistance)

            if nopl_count < 5:
                self.snap_and_save("nopl", img_folder)
                logger.debug("[NOPL] snap and save {} image".format(nopl_count + 1))
                self.snap_and_save("id", img_folder)
                logger.debug("[ID] snap and save {} image".format(id_count + 1))
                self.snap_and_save("pl", img_folder)
                logger.debug("[PL] snap and save {} image".format(pl_count + 1))
                time.sleep(0.5)
                id_count += 1
                pl_count += 1
                nopl_count += 1
            else:
                self.snap_and_save("nopl", img_folder)
                logger.debug("[NOPL] snap and save {} image".format(nopl_count + 1))
                nopl_count += 1
                time.sleep(1)
        logger.info("[IMAGE] ID = {} img, PL = {} img, NOPL = {} img".format(id_count, pl_count, nopl_count))
        logger.info("[START] camera session")


def environmental_check(cls=None):
    temp = cls.get_temperature()
    humidity = cls.get_humidity()
    illumination = cls.get_illumination()
    logger.info("Temp = {}, Humidity = {}, illumination = {}".format(temp, humidity, illumination))


def main_loop():
    with ClsPython() as cls:

        result_folder = cls.get_last_result_folder() + 1

        try:
            env_thread = PeriodicTask(10, environmental_check, cls=cls)
            env_thread.run()

            while True:
                drinking_flag, drink_amount = cls.drinking_check()
                head_flag = cls.head_check()
                logger.info("Drinking flag = {}, Head Flag = {}, drink_amount = {}".format(drinking_flag, head_flag, drink_amount))
                if drinking_flag and head_flag:
                    img_dir = cls.get_or_create_result_dir(result_folder)

                    cls.camera_session(img_dir)

                while drinking_flag:
                    drinking_flag, drink_amount = cls.drinking_check()
                    head_flag = cls.head_check()
                    if not drinking_flag and not head_flag:
                        result_folder += 1
                        break

                time.sleep(1)
        except KeyboardInterrupt:
            pass



