__author__ = 'Owner'

import os
import logging
import logging.config
from .config_loader import ClsConfig


try:
    cls_config = ClsConfig(os.getcwd())
    logging.config.fileConfig(cls_config.logging_config_path)
except AssertionError as e:
    print(e)

logger = logging.getLogger(__package__)


from .main import main_loop
from .cls_image_checker import image_checker
from .cls_calibrator import main_calibrator

main_loop = main_loop
image_checker = image_checker
calibrator = main_calibrator