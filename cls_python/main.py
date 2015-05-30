import logging
import os
import time
from datetime import datetime
from threading import Thread, Timer

import addapy
import icpy3
from icpy3.ic_exception import IC_Exception
import shutil
import decimal

from .config_loader import ClsConfig
from .utils import \
    PeriodicTask, write_csv_result, form_dct_result, \
    send_device_condition, send_device_error, retry


logger = logging.getLogger(__name__)

class ClsPython(object):
    def __init__(self):
        self.ic = icpy3.IC_ImagingControl()
        self.adda = addapy
        self.cls_config = ClsConfig(os.getcwd())
        self.id_cam = None
        self.pl_cam = None
        self.nopl_cam = None

        self.pl_display = self.cls_config.PL.getboolean("display", False)
        self.nopl_display = self.cls_config.NOPL.getboolean("display", False)
        self.id_display = self.cls_config.ID.getboolean("display", False)

        self.curr_sensor = 0
        self.total_waterflow_sensor = 0
        self.startup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def startup(self):
        self.ic.init_library()
        self.adda.Initialize_adda()
        self.adda.set_usb("on")
        self.curr_sensor = self.adda.get_flowmeter_signal()
        time.sleep(1)
        self.setup_camera()

    @retry(5, IC_Exception)
    def recover(self):
        self.cleanup()
        time.sleep(3)
        self.startup()

    def cleanup(self):
        self.ic.close_library()
        self.adda.Destroy_adda()

    def setup_camera(self):
        self.id_cam = self.ic.get_device_by_file(self.cls_config.get_id_cam_config_path())
        self.pl_cam = self.ic.get_device_by_file(self.cls_config.pl_cam_config_path)
        self.nopl_cam = self.ic.get_device_by_file(self.cls_config.nopl_cam_config_path)

        self.id_cam.start_live(show_display=self.id_display)
        self.pl_cam.start_live(show_display=self.pl_display)
        self.nopl_cam.start_live(show_display=self.nopl_display)

    def stop_camera(self):
        self.id_cam.stop_live()
        self.pl_cam.stop_live()
        self.nopl_cam.stop_live()

    def get_last_result_folder(self):
        result_dir = self.get_or_create_result_dir()
        dir_list = sorted([int(x) for x in os.listdir(result_dir)])

        if len(dir_list) > 0:
            return int(dir_list.pop())
        else:
            return 0

    def get_or_create_result_dir(self, dir_count=""):
        a = datetime.now()
        cond = self.cls_config.get_day_period()
        logger.debug("Day condition = {}".format(cond))
        logger.debug("Root result directory = {}".format(self.cls_config.MAIN["result_dir"]))
        result_dir = os.path.join(self.cls_config.MAIN["result_dir"], str(a.year), str(a.month),
                                  str(a.day), cond, str(dir_count))
        os.makedirs(result_dir, exist_ok=True)
        return result_dir

    def snap_and_save(self, cam_type, result_dir=""):
        if cam_type == "id":
            cam = self.id_cam
            prefix = self.cls_config.ID["image_prefix"]
        elif cam_type == "pl":
            cam = self.pl_cam
            prefix = self.cls_config.PL["image_prefix"]
        elif cam_type == "nopl":
            cam = self.nopl_cam
            prefix = self.cls_config.NOPL["image_prefix"]


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

    def set_led(self, kind, distance):
        if kind == "pl":
            const_a = self.cls_config.PL.getfloat("led_const_a")
            const_b = self.cls_config.PL.getfloat("led_const_b")
            const_c = self.cls_config.PL.getfloat("led_const_c")
        elif kind == "nopl":
            const_a = self.cls_config.NOPL.getfloat("led_const_a")
            const_b = self.cls_config.NOPL.getfloat("led_const_b")
            const_c = self.cls_config.NOPL.getfloat("led_const_c")
        elif kind == "reset":
            return self.adda.set_led(kind, distance, 0, 0, 0)
        return self.adda.set_led(kind, distance, const_a, const_b, const_c)

    def head_check(self):
        pl_distance = self.get_distance("pl")
        nopl_distance = self.get_distance("nopl")
        cameragap = self.cls_config.MAIN.getfloat("cameragap")
        head_width = self.cls_config.MAIN.getfloat("headwidth")
        checker = cameragap - pl_distance - nopl_distance
        logger.debug("head_width = {:4.3f}, cameragap = {:4.3f}, pl_distance = {:4.3f}, nopl_distance = {:4.3f}, checker = {:4.3f}".format(
            head_width, cameragap, pl_distance, nopl_distance, checker))
        if checker > head_width:
            return True
        else:
            return False

    def flow_check(self):
        short_sensorcount = 0
        end = time.time() + 1
        while time.time() < end:
            sensor = self.adda.get_flowmeter_signal()
            if sensor == 1 and self.curr_sensor == 0:
                short_sensorcount += 1
                self.curr_sensor = 1
            if sensor == 0 and self.curr_sensor == 1:
                short_sensorcount += 1
                self.curr_sensor = 0

        self.total_waterflow_sensor += short_sensorcount
        if short_sensorcount > self.cls_config.MAIN.getint("flowmeter_threshold"):
            return True
        else:
            return False

    def camera_session(self, img_folder):
        head_check_count = 0
        nopl_count = 0
        pl_count = 0
        id_count = 0
        timeout = time.time() + self.cls_config.MAIN.getint("image_capture_period")
        logger.info("[START] camera session")
        while time.time() < timeout:
            if not self.head_check():
                if head_check_count > 3:
                    logger.debug("[STOP] Stop due to head flag = 0")
                    break
                else:
                    head_check_count += 1

            if nopl_count < 5:
                self.snap_and_save("nopl", img_folder)
                logger.debug("[NOPL] snap and save {} image".format(nopl_count + 1))
                time.sleep(0.1)
                nopl_count += 1
            else:
                self.snap_and_save("nopl", img_folder)
                logger.debug("[NOPL] snap and save {} image".format(nopl_count + 1))
                nopl_count += 1

                if id_count < 5:
                    self.snap_and_save("id", img_folder)
                    logger.debug("[ID] snap and save {} image".format(id_count + 1))
                    id_count += 1

                if pl_count < 5:
                    self.snap_and_save("pl", img_folder)
                    logger.debug("[PL] snap and save {} image".format(pl_count + 1))
                    pl_count += 1

                time.sleep(0.5)

        logger.info("[IMAGE] ID = {} img, PL = {} img, NOPL = {} img".format(id_count, pl_count, nopl_count))
        logger.info("[FINISH] camera session")


def environmental_check(cls=None):
    header = ["datetime", "temperature", "humidity", "illumination"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp = cls.get_temperature()
    humidity = cls.get_humidity()
    illumination = cls.get_illumination()
    logger.info("Temp = {}, Humidity = {}, illumination = {}".format(temp, humidity, illumination))

    env_log_path = cls.cls_config.MAIN["environmental_log_path"]
    env_data = form_dct_result(header, [now, temp, humidity, illumination])
    logger.debug(env_data)
    write_csv_result(env_log_path, header, env_data)

def device_cleaner(cls=None):
    logger.info("[START] CLEANING Device")
    cls.adda.device_cleaning()
    logger.info("[FINISH] CLEANING Device")


def flowmeter_log(controller, img_dir, timetaken, total_flowmeter):
    header = ["folderpath", "timetaken", "total_flowmeter_signal"]
    flowmeter_log_path = controller.cls_config.MAIN["flowmeter_log_path"]
    flowmeter_data = form_dct_result(header, [img_dir, timetaken, total_flowmeter])
    logger.debug(flowmeter_data)
    write_csv_result(flowmeter_log_path, header, flowmeter_data)

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

def flow_meter(controller, stop):
    while True:
        if stop():
            break
        controller.flow_check()


def main_loop():
    with ClsPython() as cls:
        cls.get_last_result_folder()
        try:
            env_thread = PeriodicTask(cls.cls_config.MAIN.getint("environmental_check_period"),
                                      environmental_check, cls=cls)
            env_thread.run()
            device_checker_thread = PeriodicTask(cls.cls_config.MAIN.getint("environmental_check_period"),
                                      send_device_condition, main_config=cls.cls_config.MAIN)
            device_checker_thread.run()

            device_cleaner_thread = PeriodicTask(cls.cls_config.MAIN.getint("cleaning_period"),
                                      device_cleaner, cls=cls)
            device_cleaner_thread.run()

            while True:

                try:
                    result_folder = cls.get_last_result_folder() + 1
                    cls.total_waterflow_sensor = 0
                    stop_led = False
                    stop_flowmeter = False
                    drink_count = 0

                    drinking_flag = cls.flow_check()
                    head_flag = cls.head_check()
                    print("result_folder_number = {} Drinking flag = {}, Head Flag = {}".format(result_folder, drinking_flag, head_flag))
                    if drinking_flag and head_flag:
                        flowmeter_thread = Thread(target=flow_meter, args=(cls, lambda: stop_flowmeter))
                        flowmeter_thread.start()

                        led_thread = Thread(target=adjust_led, args=(cls, lambda: stop_led))
                        led_thread.start()

                        flowmeter_start_time = time.time()

                        img_dir = cls.get_or_create_result_dir(result_folder)

                        cls.camera_session(img_dir)

                        stop_led = True
                        led_thread.join()

                        stop_flowmeter = True
                        flowmeter_thread.join()

                        while True:
                            logger.info("Finish image acquisition section, waiting cattle to finish drinking")
                            drinking_flag = cls.flow_check()
                            if not drinking_flag:
                                drink_count += 1
                                print(drink_count)
                            if drink_count > 5:
                                flowmeter_end_time = time.time()
                                total_flowmeter_time = flowmeter_end_time - flowmeter_start_time
                                flowmeter_log(cls, img_dir, total_flowmeter_time, cls.total_waterflow_sensor)
                                logger.info("Finish image acquisition section, "
                                            "total_flowmeter_signal = {}".format(cls.total_waterflow_sensor))

                                result_folder += 1
                                break

                    time.sleep(1)
                except Exception as e:
                    send_device_error(cls.cls_config.MAIN, "error", "camera", e.message)
                    stop_led = True
                    led_thread.join()
                    stop_flowmeter = True
                    flowmeter_thread.join()
                    shutil.rmtree(img_dir)
                    logger.debug(e.message)
                    cls.recover()
        except KeyboardInterrupt:
            pass





