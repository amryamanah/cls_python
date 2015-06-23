__author__ = 'Owner'

import os
import json
import logging
import logging.config
from .config_loader import ClsConfig


try:
    cls_config = ClsConfig(os.getcwd())
    with open(cls_config.logging_config_path, 'rt') as f:
    	logger_config = json.load(f)
    logging.config.dictConfig(logger_config)
except AssertionError as e:
    print(e)

logger = logging.getLogger(__package__)


from .main import main_loop
from .cls_image_checker import image_checker
from .cls_calibrator import main_calibrator

main_loop = main_loop
image_checker = image_checker
calibrator = main_calibrator