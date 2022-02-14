###########################################################
#
# Main routine Plots ArticProject
# Author: Cesar Ordonez
#
###########################################################


import logging

import scr.config_logging as conflog
from scr.read_data import read_data
from scr.plot_data import plot_data

#from newmap import plot_map

#from config import ZIPDATA_PATH, UNZIPDATA_PATH

def main():
    """Execute main routines."""
    conflog.logging_config()
    conffile = conflog.read_config()
    logging.info('STEP 1: READING DATA')
    Data = read_data(conffile)
    logging.info('STEP 2: Plotting data')
    #plot_data(Data)
    # plot_map(Data)
    logging.info("***** ROUTINE COMPLETED SUCCESFULLY*****")

if __name__ == '__main__':
    main()
