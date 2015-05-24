__author__ = 'Owner'

import os
import logging
import logging.config
from .config_loader import ClsConfig

cls_config = ClsConfig(os.getcwd())

logging.config.fileConfig(cls_config.logging_config_path)
logger = logging.getLogger(__package__)

from .main import main_loop

main_loop = main_loop


