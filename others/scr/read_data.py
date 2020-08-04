###########################################################
# Reading routine
###########################################################


import logging
import os
import pandas as pd
import sys

from filecmp import dircmp
from datetime import datetime

def read_data(path_zipdata, path_unzipdata):
    """Main routine to read Mauritius data.# {{{

    Parameters
    ----------
    path_zipdata : folder directory were the data is store
    path_unzipdata: folder directory were the data processed is store

    Returns
    -------
    Dictionary with data

    """# }}}

    # if there are new data in path_zipdata
    if len(dircmp(path_zipdata, path_unzipdata).left_only) > 0:
        logging.info('Unzipping data in: %s', path_unzipdata)
        uncompress_data(path_zipdata, path_unzipdata)
    else:
        now = datetime.now()
        logging.info('There are not new data on: %s',
                now.strftime('%d-%m-%Y %H:%M'))

    logging.info('Reading LGR data')
    # TODO: CHECK IF FILES EXIST!!
    LGRdata = read_lgr(path_unzipdata)
    logging.info('Reading GPS data')
    GPSdata = read_gps(path_unzipdata)
    # logging.info('Reading EXO data')
    # read_exo(path_unzipdata)
    Data = GPSdata.join([LGRdata])
    Data = Data.reset_index()
    Data.to_csv('AllData.csv')
    return Data


def read_exo(path_unzipdata):# {{{
    """TODO: Docstring for read_exo.

    Parameters
    ----------
    path_unzipdata : TODO

    Returns
    -------
    TODO

    """
    import numpy as np

    allfiles = os.listdir(path_unzipdata)
    for datefile in allfiles:
        datefile_path = os.path.join(path_unzipdata, datefile)
        exofile = [x for x in os.listdir(datefile_path) if ".bin" in x][0]
        exofile_path = os.path.join(datefile_path, exofile)
        dt = np.dtype([('Date', 'str'), ('Time', 'str'), ('Time_fract', 'int'),
            ('Site', 'float'), ('a', 'int'), ('b', 'float'), ('c', 'float'),
            ('Temp', 'float'), ('Cond', 'float'), ('Sp', 'float'), ('Sal', 'float'), ('nfl cond', 'float'), ('TDS', 'float'), ('ODOsat', 'float'), ('ODO', 'float'), ('Press', 'float'), ('Depth', 'float')])
        with open(exofile_path, 'rb') as f:
            npdata = np.fromfile(f, dtype=dt)#np.dtype('B'))
        print(npdata[0:40])
        __import__('pdb').set_trace()
        """
        with open(exofile_path, 'rb') as f:
            byte = f.read(1)
            while byte:
                byte = f.readline()
                print(byte)
                __import__('pdb').set_trace()
        """

    pass# }}}

def read_gps(path_unzipdata):# {{{
    """TODO: Docstring for read_gps.{{{

    Parameters
    ----------
    path_unzipdata: folder directory were the data processed is store

    Returns
    -------
    data: dataframe with gps data

    """# }}}
    import gpxpy
    import gpxpy.gpx

    allfiles = os.listdir(path_unzipdata)
    time = []
    lat = []
    lon = []
    for datefolder in allfiles:
        logging.info('Reading data: %s', datefolder)
        datefolder_path = os.path.join(path_unzipdata, datefolder)
        gpsfolder = [x for x in os.listdir(datefolder_path) if 'GPS' in x]
        try:
            gpsfolder = gpsfolder[0]
        except IndexError:
            logging.warning('YB folder does not found in: %s', datefolder_path)
            continue
        gpsfolder_path = os.path.join(datefolder_path, gpsfolder)
        for gpsfile in os.listdir(gpsfolder_path):
            gpxfile = open(os.path.join(gpsfolder_path, gpsfile), 'r')
            gpx = gpxpy.parse(gpxfile)
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        time.append(point.time.replace(tzinfo=None))
                        lat.append(point.latitude)
                        lon.append(point.longitude)
    d = {'Datetime': time, 'Latitude': lat, 'Longitude': lon}
    data = pd.DataFrame(data=d)
    data = data.set_index('Datetime')
    data = data.resample("1T").mean()
    return data# }}}

def append_pddata(i, data, newdata):# {{{
    if i == 0:
        data = newdata
    else:
        data = pd.concat([data, newdata], axis=0)
    return data# }}}

def read_lgr(newpath):# {{{
    """Reading LGR file
    """
    def footer_pos(LGRfile):# {{{
        import zipfile
        import io
        """find footer position
        """

        zipf = zipfile.ZipFile(LGRfile)
        f = zipf.namelist()[0]
        content = io.BytesIO(zipf.read(f))
        i = 0
        foot = False
        for line in content.readlines(): #zipf.read(f): #zipf.read(f):
            if line.startswith(b'-----B'):
                ib = i
                foot = True
            i += 1
        if foot:
            ifooter = i - ib
        else:
            ifooter = 0
        return ifooter# }}}
    data = []
    i = 0
    for alldata in os.listdir(newpath):
        allfiles = os.path.join(newpath, alldata)
        LGRfolderdata = [x for x in os.listdir(allfiles) if any(s in x for s in ('YB', 'GHG'))]
        try:
            LGRfolderdata = LGRfolderdata[0]
        except IndexError:
            logging.warning('YB or GHG folder does not found in: %s', allfiles)
            continue
        LGRdatadate = os.path.join(allfiles, LGRfolderdata)
        folderdates = os.listdir(LGRdatadate)
        for date in sorted(folderdates)[:-1]: #NOT READING LAST DATE IN ZIPFILE
            datadate = os.path.join(LGRdatadate, date)
            filedate = os.listdir(datadate)
            for lgrfile in filedate:
                logging.info('Reading file: %s', lgrfile)
                readfile = os.path.join(datadate, lgrfile)
                ifoot = footer_pos(readfile)
                ## Reading column 0 is time, column 7 [CH4]d_ppm and column 9 [CO2]d_ppm
                rfile = pd.read_csv(readfile, sep=',', header=1, skipfooter=ifoot,
                        squeeze=True, infer_datetime_format=True, parse_dates=[0],
                        usecols=[0, 7, 9], engine='python', index_col=[0], names=['Time', 'CH4d_ppm', 'CO2d_ppm'])
                data = append_pddata(i, data, rfile)
                i += 1
    data = data.sort_index()
    data = data.resample("1T").mean()
    return data# }}}

def copy_filelike_to_filelike(src, dst, bufsize=16384):# {{{
    while True:
        buf = src.read(bufsize)
        if not buf:
            break
        dst.write(buf)# }}}

def uncompress_data(path_zipdata, path_unzipdata, rec=False):# {{{
    """Routine to unzip data.# {{{

    Parameters
    ----------
    path_zipdata : folder directory were the data is store
    path_unzipdata: folder directory were the data processed is store

    Returns
    -------
    newunzipfile:

    """# }}}
    import zipfile
    import io
    import shutil

    zipfiles = os.listdir(path_zipdata)
    unzipfiles = os.listdir(path_unzipdata)

    # Check new files in zipfolder (not processed before)
    newfiles = [newf for newf in zipfiles if newf not in unzipfiles] # and zipfile.is_zipfile(newf)]
    for newf in newfiles:
        newzipfiles = os.path.join(path_zipdata, newf)
        if zipfile.is_zipfile(newzipfiles): # newf = New big batch/date of data
            logging.info('Unzip data: %s', newf)
            newunzipfile = os.path.join(path_unzipdata, newf)
            z = zipfile.ZipFile(newzipfiles) # files inside new date data
            for f in z.namelist():
                logging.info('Unzip data: %s', f)
                newunzipfile2 = os.path.join(newunzipfile, f) #folder inside instrument zipfile
                newzipfile2 = os.path.join(newzipfiles, f)
                content = io.BytesIO(z.read(f)) # read content as byte
                # TODO: CHECK IF FALE READING OR COPY FILES
                if zipfile.is_zipfile(newunzipfile2):# in newunzipfile2[-5:]:
                    zip_file = zipfile.ZipFile(content)
                    if not os.path.exists(newunzipfile2):
                        os.makedirs(newunzipfile2)
                    for i in zip_file.namelist():
                        zip_file.extract(i, newunzipfile2)
                else:
                    if not os.path.exists(newunzipfile):
                        os.makedirs(newunzipfile)
                    with open(newunzipfile, "wb") as outfile:
                        copy_filelike_to_filelike(content, outfile)
