__author__ = 'Owner'

import os
from configparser import ConfigParser
from datetime import datetime


def config_assert(config_item):
    assert os.path.exists(config_item), "{} file does not exist in cls_config folder".format(config_item)


class ClsConfig(object):
    def __init__(self, root_folder):
        self.root_folder_path = root_folder

        self.config_folder_path = os.path.join(self.root_folder_path, "cls_config")
        assert os.path.exists(self.config_folder_path), \
            "config_folder ({}) does not exist".format(self.config_folder_path)

        self.cls_config_path = self._set_config_item("cls_python.ini")
        self.pl_cam_config_path = self._set_config_item("PLCamera.xml")
        self.nopl_cam_config_path = self._set_config_item("NOPLCamera.xml")
        self.day_id_cam_config_path = self._set_config_item("DayIDCamera.xml")
        self.night_id_cam_config_path = self._set_config_item("NightIDCamera.xml")
        self.parser = self.read_config()
        self.MAIN = self.parser["MAIN"]
        self.ID = self.parser["ID"]
        self.PL = self.parser["PL"]
        self.NOPL = self.parser["NOPL"]
        self.TEMPERATURE = self.parser["TEMPERATURE"]
        self.ILLUMINATION = self.parser["ILLUMINATION"]
        self.HUMIDITY = self.parser["HUMIDITY"]

    def _set_config_item(self, suffix_path):
        item = os.path.join(self.config_folder_path, suffix_path)
        assert os.path.exists(item), "{} file does not exist in cls_config folder".format(item)
        return item

    def read_config(self):
        parser = ConfigParser()
        parser.read(self.cls_config_path)
        return parser

    def get_day_period(self):
        cur_hour = datetime.now().hour
        daytime_limit_hour = self.MAIN.getint("daytime_limit")
        nighttime_limit_hour = self.MAIN.getint("nighttime_limit")

        if daytime_limit_hour < cur_hour < nighttime_limit_hour:
            return "nighttime"
        else:
            return "daytime"

    def get_id_cam_config_path(self):
        curr_period = self.get_day_period()
        if curr_period == "nighttime":
            return self.night_id_cam_config_path
        else:
            return self.day_id_cam_config_path



