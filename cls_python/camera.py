__author__ = 'amryf'

from icpy3 import IC_ImagingControl, IC_Exception
from datetime import datetime
import os


def snap_and_save(cam, prefix, result_dir):
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
        cam.save_image(img_path,0)
        print(img_path)
    except IC_Exception as e:
        print(e.message)


def get_or_create_result_dir(dir_count, root_dir):
        a = datetime.now()
        if a.hour in range(0,18):
            cond = "day"
        else:
            cond = "night"
        result_dir =  os.path.join(root_dir, str(a.year), str(a.month), str(a.day), cond, str(dir_count))
        os.makedirs(result_dir, exist_ok=True)
        return result_dir

if __name__ == "__main__":

    ic = IC_ImagingControl()
    ic.init_library()
    root_dir = "result"


    id_cam = ic.get_device_by_file("IDCamera.xml")
    id_cam.start_live()
    for folder_num in range(1,4):
        for photo_num in range(1,40):
            result_dir = get_or_create_result_dir(folder_num, root_dir)
            snap_and_save(id_cam,"id",result_dir)
    id_cam.stop_live()
    ic.close_library()

