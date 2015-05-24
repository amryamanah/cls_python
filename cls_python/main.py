import logging
import os
import time
from datetime import datetime
from threading import Thread

import addapy
import icpy3

from .config_loader import ClsConfig
from .utils import PeriodicTask, write_csv_result, form_dct_result


logger = logging.getLogger(__name__)


class ClsPython(object):
    def __init__(self):
        self.ic = icpy3.IC_ImagingControl()
        self.adda = addapy
        self.cls_config = ClsConfig(os.getcwd())
        self.id_cam = None
        self.pl_cam = None
        self.nopl_cam = None
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

    def flow_check_onetime(self, sensor_prev):  # todo check the drinking algorithm
        # todo check the drinking algorithm
        """
            check drinking
        """
        sensor = self.adda.get_flowmeter_signal()
        if sensor == 1 and sensor_prev == 0:
            self.total_waterflow_sensor += 1
            sensor_prev = 1
        if sensor == 0 and sensor_prev == 1:
            self.total_waterflow_sensor += 1
            sensor_prev = 0
        return sensor_prev

    def flow_check(self):
        sensor_prev = self.adda.flow_check()
        short_sensorcount = 0
        end = time.time() + 0.3
        while time.time() < end:
            sensor = self.adda.flow_check()
            if sensor == 1 and sensor_prev == 0:
                short_sensorcount += 1
                sensor_prev = 1
            if sensor == 0 and sensor_prev == 1:
                short_sensorcount += 1
                sensor_prev = 0

        self.total_waterflow_sensor += short_sensorcount
        if short_sensorcount > self.cls_config.MAIN.getint("flowmeter_threshold"):
            return True
        else:
            return False

    def camera_session(self, img_folder):
        nopl_count = 0
        pl_count = 0
        id_count = 0
        timeout = time.time() + self.cls_config.MAIN.getint("image_capture_period")
        logger.info("[START] camera session")
        while time.time() < timeout:
            if not self.head_check():
                logger.debug("[STOP] Stop due to head flag = 0")
                break
            if nopl_count < 5:
                self.snap_and_save("nopl", img_folder)
                logger.debug("[NOPL] snap and save {} image".format(nopl_count + 1))
                time.sleep(0.2)
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
    logger.debug("Temp = {}, Humidity = {}, illumination = {}".format(temp, humidity, illumination))

    env_log_path = cls.cls_config.MAIN["environmental_log_path"]
    env_data = form_dct_result(header, [now, temp, humidity, illumination])
    logger.debug(env_data)
    write_csv_result(env_log_path, header, env_data)

def flowmeter_log(controller, img_dir, timetaken, total_flowmeter):
    header = ["folderpath", "timetaken", "total_flowmeter_signal"]
    flowmeter_log_path = controller.cls_config.MAIN["flowmeter_log_path"]
    flowmeter_data = form_dct_result(header, [img_dir, timetaken, total_flowmeter])
    logger.debug(flowmeter_data)
    write_csv_result(flowmeter_log_path, header, flowmeter_data)
    pass

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

        result_folder = cls.get_last_result_folder() + 1

        try:
            env_thread = PeriodicTask(cls.cls_config.MAIN.getint("environmental_check_period"),
                                      environmental_check, cls=cls)
            env_thread.run()

            while True:

                stop_led = False
                stop_flowmeter = False

                drinking_flag = cls.flow_check()
                head_flag = cls.head_check()
                print("Drinking flag = {}, Head Flag = {} cls.total_waterflow_sensor = {}".format(
                    drinking_flag, head_flag, cls.total_waterflow_sensor
                ))
                if drinking_flag and head_flag:
                    flowmeter_thread = Thread(target=flow_meter, args=(cls, lambda: stop_flowmeter))
                    flowmeter_thread.start()

                    img_dir = cls.get_or_create_result_dir(result_folder)
                    flowmeter_start_time = time.time()

                    led_thread = Thread(target=adjust_led, args=(cls, lambda: stop_led))
                    led_thread.start()

                    cls.camera_session(img_dir)

                    stop_led = True
                    led_thread.join()

                    stop_flowmeter = True
                    flowmeter_thread.join()

                    while drinking_flag :
                        logger.debug("Finish image acquisition section, waiting cattle to finish drinking")
                        drinking_flag = cls.flow_check()
                        if not drinking_flag:
                            flowmeter_end_time = time.time()
                            total_flowmeter_time = flowmeter_end_time - flowmeter_start_time
                            flowmeter_log(cls, img_dir, total_flowmeter_time, cls.total_waterflow_sensor)
                            logger.debug("Finish image acquisition section, "
                                         "total_flowmeter_signal = {}".format(cls.total_waterflow_sensor))
                            cls.total_waterflow_sensor = 0
                            result_folder += 1
                            break

                time.sleep(1)
        except KeyboardInterrupt:
            pass



