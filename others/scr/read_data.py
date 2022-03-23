###########################################################
# Reading routine
###########################################################


import logging
import os
import zipfile as zf
from datetime import datetime

import matplotlib.pyplot as plt

import pandas as pd


def read_data(conffile):
    """Main routine to read Mauritius data.# {{{

    Parameters
    ----------
    conffile: configuration file
    Returns
    -------
    Dictionary with data

    """# }}}

    path_zipdata = conffile['paths']['zip']
    path_unzipdata = conffile['paths']['unzip']
    path_exo2 = conffile['paths']['exopath']
    # if there are new data in path_zipdata
    if conffile['readprofile']:
        filename = os.path.join(conffile['paths']['filepath'], conffile['files']['datafile'])
        data = pd.read_csv(filename, parse_dates=[1])
    else:
        zipfiles = os.listdir(path_zipdata)
        unzipfiles = os.listdir(path_unzipdata)
        unzipfiles = list(map(lambda x: x.capitalize(), unzipfiles))
        # Check new files in zipfolder (not processed before)
        newfiles = [newf for newf in zipfiles if newf[:-4].capitalize() not in unzipfiles]
        if len(newfiles) > 0:
            logging.info('Unzipping data in: %s', path_unzipdata)
            uncompress_data(path_zipdata, path_unzipdata)
        else:
            now = datetime.now()
            logging.info('There are not new data on: %s',
                    now.strftime('%d-%m-%Y %H:%M'))

        logging.info('Reading GPS data')
        GPSdata = read_gps(path_unzipdata)

        # TODO: CHECK IF FILES EXIST!!
        logging.info('Reading LGR data')
        LGRdata = read_lgr(path_unzipdata)
        logging.info('Reading EXO data')
        exodata = read_oldexo(path_unzipdata, path_exo2)
        if GPSdata.empty and exodata.empty:
            data = LGRdata
        elif GPSdata.empty:
            data = LGRdata.join([exodata])
        elif exodata.empty:
            data = LGRdata.join([GPSdata])
        else:
            data = LGRdata.join([GPSdata, exodata])
        #for col in LGRdata.columns:
        #    fig, ax = plt.subplots(1, 1, figsize=(5,3))
        #    LGRdata[col].plot()
        #    ax.set_ylabel(col)
        #    ax.set_xlabel('')
        #    plt.tight_layout()
        #    fig.savefig(col + '.png', format='png', dpi=300)
        #__import__('pdb').set_trace()
        #data = GPSdata.join([LGRdata])
        data = data.resample('10T').mean()
        data = data.reset_index()
        data.to_csv(conffile['files']['datafile'])
    return data


def read_exo(path_unzipdata):# {{{
    """TODO: Docstring for read_exo.

    Parameters
    ----------
    path_unzipdata : TODO

    Returns
    -------
    TODO

    """

    allfiles = os.listdir(path_unzipdata)
    i = 0
    data = []
    for datefile in allfiles:
        datefile_path = path_unzipdata #os.path.join(path_unzipdata, datefile)
        exofiles = [x for x in os.listdir(datefile_path) if ".csv" in x]
        for exofile in exofiles:
            exofile_path = os.path.join(datefile_path, exofile)
            logging.info('Reading file: %s' % exofile_path)
            try:
                exodata = pd.read_csv(exofile_path, sep=',', encoding='utf-16', skiprows=9)
            except Exception:
                exodata = pd.read_csv(exofile_path, sep=',', encoding='utf-8', skiprows=8)
            exodata = exodata.dropna()
            exodata = exodata.set_index('Date (MM/DD/YYYY)')
            if 'Date (MM/DD/YYYY)' in exodata.index.values:
                exodata = exodata.drop('Date (MM/DD/YYYY)', axis=0)
            exodata = exodata.reset_index()
            exodata['Datetime'] = pd.to_datetime(exodata['Date (MM/DD/YYYY)'] + ' ' + exodata['Time (HH:mm:ss)'], format='%m/%d/%Y %H:%M:%S')
            data = append_pddata(i, data, exodata)
            i += 1
    data = data.drop(['Site Name', 'Date (MM/DD/YYYY)', 'Time (HH:mm:ss)'], axis=1)
    data = data.set_index('Datetime')
    data = data.sort_index()
    data = data.astype(float)
    data = data.resample("1T").mean()
    return data #}}}


def read_oldexo(path_unzipdata, path_exo2):# {{{
    """TODO: Docstring for read_exo.

    Parameters
    ----------
    path_unzipdata : TODO
    path_exo2: TODO

    Returns
    -------
    TODO

    """

    i = 0
    data = []
    datefile_path = os.path.join(path_exo2)
    exofiles = [x for x in os.listdir(datefile_path) if ".xls" in x]
    for exofile in exofiles:
        exofile_path = os.path.join(datefile_path, exofile)
        logging.info('Reading file: %s' % exofile_path)
        idx = find_firstcol(exofile_path)
        exodata = pd.read_excel(exofile_path, skiprows=idx, parse_dates=[['Date (MM/DD/YYYY)', 'Time (HH:MM:SS)']])

        #exodata = exodata.dropna()
        #exodata = exodata.set_index('Date (MM/DD/YYYY)')
        #if 'Date (MM/DD/YYYY)' in exodata.index.values:
        #    exodata = exodata.drop('Date (MM/DD/YYYY)', axis=0)
        #exodata = exodata.reset_index()
        #exodata['Datetime'] = 
        #pd.to_datetime(exodata['Date (MM/DD/YYYY)'].dt.strftime('%m/%d/%Y') + ' ' + exodata['Time (HH:MM:SS)'], format='%m/%d/%Y %H:%M:%S')
        data = append_pddata(i, data, exodata)
        i += 1
    if not pd.DataFrame(data).empty:
        data = data.drop(['Site Name'], axis=1)# 'Date (MM/DD/YYYY)', 'Time (HH:mm:ss)'], axis=1)
        data.rename(columns={'Date (MM/DD/YYYY)_Time (HH:MM:SS)':'Datetime'}, inplace=True)
        data = data.set_index('Datetime')
        data = data.sort_index()
        data = data.astype(float)
        data = data.resample("1T").mean()
    else:
        data = pd.DataFrame(data)
    return data #}}}
    """# {{{
    dt = np.dtype([('Date', 'str'), ('Time', 'str'), ('Time_fract', 'int'),
        ('Site', 'float'), ('a', 'int'), ('b', 'float'), ('c', 'float'),
        ('Temp', 'float'), ('Cond', 'float'), ('Sp', 'float'), ('Sal', 'float'), ('nfl cond', 'float'), ('TDS', 'float'), ('ODOsat', 'float'), ('ODO', 'float'), ('Press', 'float'), ('Depth', 'float')])
    with open(exofile_path, 'rb') as f:
        npdata = np.fromfile(f, dtype=dt)#np.dtype('B'))
    print(npdata[0:40])
    __import__('pdb').set_trace()
    with open(exofile_path, 'rb') as f:
        byte = f.read(1)
        while byte:
            byte = f.readline()
            print(byte)
            __import__('pdb').set_trace()
    """# }}}

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
            logging.warning('GPS folder does not found in: %s', datefolder_path)
            continue
        gpsfolder_path = os.path.join(datefolder_path, gpsfolder)
        for gpsfile in os.listdir(gpsfolder_path):
            logging.info('Reading file: %s' % gpsfile)
            try:
                gpxfile = open(os.path.join(gpsfolder_path, gpsfile), 'r')
                gpx = gpxpy.parse(gpxfile)
                for track in gpx.tracks:
                    for segment in track.segments:
                        for point in segment.points:
                            try:
                                time.append(point.time.replace(tzinfo=None))
                                lat.append(point.latitude)
                                lon.append(point.longitude)
                            except Exception:
                                logging.warning('GPS point without time value: lat %.1f lon %.1f' % (point.latitude, point.longitude))
            except Exception:
                logging.error('No GPS file for: %s', datefolder)
    d = {'Datetime': time, 'Latitude': lat, 'Longitude': lon}
    data = pd.DataFrame(data=d)
    data = data.set_index('Datetime')
    if not data.empty:
        data = data.resample("1T").mean()
    else:
        data = pd.DataFrame(data)
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
    custom_parser = lambda x: datetime.strptime(x, "%m/%d/%Y %H:%M:%S.%f")
    for alldata in os.listdir(newpath):
        allfiles = os.path.join(newpath, alldata)
        LGRfolderdata = [x for x in os.listdir(allfiles) if any(s in x for s in ('YB', 'AtmGHG', 'atmGHG'))]
        try:
            LGRfolderdata = LGRfolderdata[0]
        except IndexError:
            logging.warning('YB or GHG folder does not found in: %s', allfiles)
            continue
        LGRdatadate = os.path.join(allfiles, LGRfolderdata)
        folderdates = os.listdir(LGRdatadate)
        for date in sorted(folderdates): #NOT READING LAST DATE IN ZIPFILE
            datadate = os.path.join(LGRdatadate, date)
            filedate = os.listdir(datadate)
            for lgrfile in filedate:
                logging.info('Reading file: %s', lgrfile)
                readfile = os.path.join(datadate, lgrfile)
                ifoot = footer_pos(readfile)
                ## Reading column 0 is time, column 7 [CH4]d_ppm and column 9 [CO2]d_ppm
                rfile = pd.read_csv(readfile, sep=',', header=1, skipfooter=ifoot,
                        squeeze=True,skipinitialspace=True, parse_dates=[0], index_col=[0], date_parser=custom_parser,
                        usecols=[0, 3, 7, 9, 11, 13, 17, 19], engine='python', names=['Datetime', 'H20_ppm', 'CH4d_ppm', 'CO2d_ppm', 'GasP_torr', 'GasT_C', 'RD0_us', 'RD1_us'])
                #rfile['Time'] = pd.to_datetime(rfile['Time'], format='%m/%d/%Y %H:%M:%S.%f')
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

    zipfiles = os.listdir(path_zipdata)
    unzipfiles = os.listdir(path_unzipdata)
    unzipfiles = list(map(lambda x: x.capitalize(), unzipfiles))
    #zipfiles = list(map(lambda x: x.capitalize(), zipfiles))
    # Check new files in zipfolder (not processed before)
    newfiles = [newf for newf in zipfiles if newf[:-4].capitalize() not in unzipfiles] # and zipfile.is_zipfile(newf)]
    for newf in newfiles:
        newzipfiles = os.path.join(path_zipdata, newf)
        if zf.is_zipfile(newzipfiles): # newf = New big batch/date of data
            logging.info('Unzip data: %s', newf)
            newunzipfile = os.path.join(path_unzipdata, newf)
            z = zf.ZipFile(newzipfiles) # files inside new date data
            z.extractall(path_unzipdata)
            # for f in z.namelist():
            #     logging.info('Unzip data inside: %s', f)
            #     newunzipfile2 = os.path.join(newunzipfile, f) #folder inside instrument zipfile
            #     newzipfile2 = os.path.join(newzipfiles, f)
            #     content = io.BytesIO(z.read(f)) # read content as byte
            #     # TODO: CHECK IF FALE READING OR COPY FILES
            #     if zf.is_zipfile(newunzipfile2):# in newunzipfile2[-5:]:
            #         zip_file = zf.ZipFile(content)
            #         if not os.path.exists(newunzipfile2):
            #             os.makedirs(newunzipfile2)
            #         for i in zip_file.namelist():
            #             zip_file.extract(i, newunzipfile2)
            #     else:
            #         if not os.path.exists(newunzipfile):
            #             os.makedirs(newunzipfile)
            #         with open(newunzipfile, "wb") as outfile:
            #             copy_filelike_to_filelike(content, outfile)
    #}}}

def find_firstcol(filename):
    data = pd.read_excel(filename)
    firstcol = data.columns[0]
    idx = data[data[firstcol] == 'Date (MM/DD/YYYY)'].index.values[0]
    return idx + 1
