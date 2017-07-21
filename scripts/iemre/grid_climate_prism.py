"""Grid climate for netcdf usage"""
from __future__ import print_function
import sys
import datetime

import netCDF4
import numpy as np
import psycopg2
from pyiem import iemre, datatypes
from pyiem.network import Table as NetworkTable
from pyiem.reference import state_names
from scipy.interpolate import NearestNDInterpolator

NT = NetworkTable(["%sCLIMATE" % (abbr, ) for abbr in state_names])
COOP = psycopg2.connect(database='coop', user='nobody', host='iemdb')


def generic_gridder(nc, cursor, idx):
    """
    Generic gridding algorithm for easy variables
    """
    lats = []
    lons = []
    vals = []
    for row in cursor:
        if row[idx] is not None and row['station'] in NT.sts:
            lats.append(NT.sts[row['station']]['lat'])
            lons.append(NT.sts[row['station']]['lon'])
            vals.append(row[idx])
    if len(vals) < 4:
        print(("Only %s observations found for %s, won't grid"
               ) % (len(vals), idx))
        return None

    xi, yi = np.meshgrid(nc.variables['lon'][:], nc.variables['lat'][:])
    nn = NearestNDInterpolator((lons, lats), np.array(vals))
    grid = nn(xi, yi)
    print(("%s %s %.3f %.3f"
           ) % (cursor.rowcount, idx, np.max(grid), np.min(grid)))
    if grid is not None:
        return grid
    return None


def grid_day(nc, ts):
    """
    I proctor the gridding of data on an hourly basis
    @param ts Timestamp of the analysis, we'll consider a 20 minute window
    """
    cursor = COOP.cursor(cursor_factory=psycopg2.extras.DictCursor)
    offset = iemre.daily_offset(ts)
    if ts.day == 29 and ts.month == 2:
        ts = datetime.datetime(2000, 3, 1)

    sql = """SELECT * from ncdc_climate71 WHERE valid = '%s' and
             substr(station,3,4) != '0000' and substr(station,3,1) != 'C'
             """ % (ts.strftime("%Y-%m-%d"), )
    cursor.execute(sql)
    if cursor.rowcount > 4:
        res = generic_gridder(nc, cursor, 'high')
        if res is not None:
            nc.variables['tmax'][offset] = datatypes.temperature(
                                                        res,
                                                        'F').value('C')
        cursor.scroll(0, mode='absolute')
        res = generic_gridder(nc, cursor, 'low')
        if res is not None:
            nc.variables['tmin'][offset] = datatypes.temperature(
                                                        res,
                                                        'F').value('C')
        cursor.scroll(0, mode='absolute')
        res = generic_gridder(nc, cursor, 'precip')
        if res is not None:
            nc.variables['ppt'][offset] = datatypes.distance(res,
                                                             'IN').value('MM')
    else:
        print(("%s has %02i entries, FAIL"
               ) % (ts.strftime("%Y-%m-%d"), cursor.rowcount))


def workflow(ts):
    # Load up a station table we are interested in

    # Load up our netcdf file!
    nc = netCDF4.Dataset("/mesonet/data/prism/prism_dailyc.nc", 'a')
    grid_day(nc, ts)
    nc.close()


def main(argv):
    """Go Main!"""
    if len(argv) == 4:
        ts = datetime.datetime(int(argv[1]), int(argv[2]),
                               int(argv[3]))
        workflow(ts)
    else:
        sts = datetime.datetime(2000, 1, 1)
        ets = datetime.datetime(2001, 1, 1)
        interval = datetime.timedelta(days=1)
        now = sts
        while now < ets:
            print(now)
            workflow(now)
            now += interval


if __name__ == "__main__":
    main(sys.argv)
