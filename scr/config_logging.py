#!/usr/bin/env python

import logging

def logging_config():
    """Configure logging.

    Returns
    -------

    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:> %(message)s',
                        datefmt='%d/%m/%y %H:%M')
