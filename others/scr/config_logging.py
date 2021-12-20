#!/usr/bin/env python

import logging
import yaml

def logging_config():
    """Configure logging.

    Returns
    -------

    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:> %(message)s',
                        datefmt='%d/%m/%y %H:%M')

def read_config():
    with open('config.yml', 'r') as file:
        conf_model = yaml.safe_load(file)
    return conf_model
