from .adda import main_adda
from icpy3 import IC_ImagingControl, IC_Exception
from os import system
from . import _cls_config


def main_loop():
    ic = IC_ImagingControl()
    ic.init_library()
    root_dir = "result"
    id_cam = ic.get_device_by_file(_cls_config.get_id_cam_config_path())
    pl_cam = ic.get_device_by_file(_cls_config.pl_cam_config_path)
    nopl_cam = ic.get_device_by_file(_cls_config.nopl_cam_config_path)
