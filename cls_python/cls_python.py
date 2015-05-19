from time import sleep, clock
import addapy
from icpy3 import IC_ImagingControl, IC_Exception
from datetime import datetime
from .config_loader import ClsConfig
import os
import decorator
from IPython import embed


def retry(howmany, *exception_types, **kwargs):
    timeout = kwargs.get('timeout', 0.0) # seconds
    @decorator.decorator
    def tryIt(func, *fargs, **fkwargs):
        for _ in range(howmany):
            try: return func(*fargs, **fkwargs)
            except exception_types or Exception:
                if timeout is not None:
                    sleep(timeout)
    return tryIt


class ClsPython(object):
    def __init__(self):
        self.ic = IC_ImagingControl()
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
            print(img_path)
        except IC_Exception as e:
            print(e.message)

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

    def head_check(self, pl_distance, nopl_distance):
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
        sensorprev = self.adda.get_waterflow_signal()
        short_sensorcount = 0
        t3 = clock()
        it = 0
        while it < 300:
            t2 = clock()
            if t2-t3 > it:
                sensor = self.adda.get_waterflow_signal()
                if sensor == 1 and sensorprev == 0:
                    short_sensorcount += 1
                    sensorprev = 1
                if sensor == 0 and sensorprev == 1:
                    short_sensorcount += 1
                    sensorprev = 0
            it += 1

        if short_sensorcount > flowmeter_threshold:
            return 1, short_sensorcount
        else:
            return 0, short_sensorcount


def take_picture(cls, result_folder):
    result_dir = cls.get_or_create_result_dir(result_folder)
    cls.snap_and_save("id", result_dir)
    cls.snap_and_save("pl", result_dir)
    cls.snap_and_save("nopl", result_dir)


def main_loop():
    with ClsPython() as cls:

        result_folder = cls.get_last_result_folder() + 1

        try:
            while True:
                drinking_flag, drink_amount = cls.drinking_check()
                #drinking_flag, drink_amount = 1,1
                temp = cls.get_temperature()
                humidity = cls.get_humidity()
                illumination = cls.get_illumination()

                print("Drinking flag = {}, Drinking amount = {}".format(drinking_flag, drink_amount))
                print("Temp = {}, Humidity = {}, illumination = {}".format(
                    temp, humidity, illumination
                ))
                if drinking_flag:
                    pl_distance = cls.get_distance("pl")
                    no_pldistance = cls.get_distance("nopl")
                    head_flag = cls.head_check(pl_distance, no_pldistance)
                    print("Head Flag = {}, pl_distance = {}, nopl_distance = {}".format(
                        head_flag, pl_distance, no_pldistance
                    ))
                    if head_flag:
                        cls.set_led("pl", pl_distance)
                        cls.set_led("nopl", no_pldistance)
                    else:
                        cls.set_led("reset", 0)
                else:
                    sleep(1)
        except KeyboardInterrupt:
            pass


            # for folder_num in range(1,4):
            #     for photo_num in range(1,40):
            #         result_dir = cls.get_or_create_result_dir(result_folder)
            #         cls.snap_and_save("id", result_dir)
            #         cls.snap_and_save("pl", result_dir)
            #         cls.snap_and_save("nopl", result_dir)
            #     result_folder += 1

        #cls.adda.device_cleaning()


