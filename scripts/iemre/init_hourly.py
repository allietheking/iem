"""Generate the IEMRE hourly analysis file for a year"""
from __future__ import print_function
import datetime
import sys

import geopandas as gpd
import numpy as np
from pyiem import iemre
from pyiem.grid.zs import CachingZonalStats
from pyiem.util import get_dbconn, ncopen


def init_year(ts):
    """
    Create a new NetCDF file for a year of our specification!
    """

    fn = iemre.get_hourly_ncname(ts.year)
    nc = ncopen(fn, 'w')
    nc.title = "IEM Hourly Reanalysis %s" % (ts.year,)
    nc.platform = "Grided Observations"
    nc.description = "IEM hourly analysis on a 0.125 degree grid"
    nc.institution = "Iowa State University, Ames, IA, USA"
    nc.source = "Iowa Environmental Mesonet"
    nc.project_id = "IEM"
    nc.realization = 1
    nc.Conventions = 'CF-1.0'
    nc.contact = "Daryl Herzmann, akrherz@iastate.edu, 515-294-5978"
    nc.history = ("%s Generated"
                  ) % (datetime.datetime.now().strftime("%d %B %Y"),)
    nc.comment = "No Comment at this time"

    # Setup Dimensions
    nc.createDimension('lat', iemre.NY)
    nc.createDimension('lon', iemre.NX)
    ts2 = datetime.datetime(ts.year + 1, 1, 1)
    days = (ts2 - ts).days
    print('Year %s has %s days' % (ts.year, days))
    nc.createDimension('time', int(days) * 24)

    # Setup Coordinate Variables
    lat = nc.createVariable('lat', np.float, ('lat',))
    lat.units = "degrees_north"
    lat.long_name = "Latitude"
    lat.standard_name = "latitude"
    lat.axis = "Y"
    lat[:] = iemre.YAXIS

    lon = nc.createVariable('lon', np.float, ('lon',))
    lon.units = "degrees_east"
    lon.long_name = "Longitude"
    lon.standard_name = "longitude"
    lon.axis = "X"
    lon[:] = iemre.XAXIS

    tm = nc.createVariable('time', np.float, ('time',))
    tm.units = "Hours since %s-01-01 00:00:0.0" % (ts.year,)
    tm.long_name = "Time"
    tm.standard_name = "time"
    tm.axis = "T"
    tm.calendar = "gregorian"
    tm[:] = np.arange(0, int(days) * 24)

    # Tracked variables
    hasdata = nc.createVariable('hasdata', np.int8, ('lat', 'lon'))
    hasdata.units = '1'
    hasdata.long_name = 'Analysis Available for Grid Cell'
    hasdata.coordinates = "lon lat"
    hasdata[:] = 0

    # can storage -128->127 actual values are 0 to 100
    skyc = nc.createVariable('skyc', np.int8, ('time', 'lat', 'lon'),
                             fill_value=-128)
    skyc.long_name = "ASOS Sky Coverage"
    skyc.stanard_name = "ASOS Sky Coverage"
    skyc.units = "%"
    skyc.valid_range = [0, 100]
    skyc.coordinates = "lon lat"

    # 0->65535
    tmpk = nc.createVariable('tmpk', np.uint16, ('time', 'lat', 'lon'),
                             fill_value=65535)
    tmpk.units = "K"
    tmpk.scale_factor = 0.01
    tmpk.long_name = "2m Air Temperature"
    tmpk.standard_name = "2m Air Temperature"
    tmpk.coordinates = "lon lat"

    # 0->65535  0 to 655.35
    dwpk = nc.createVariable('dwpk', np.uint16, ('time', 'lat', 'lon'),
                             fill_value=65335)
    dwpk.units = "K"
    dwpk.scale_factor = 0.01
    dwpk.long_name = "2m Air Dew Point Temperature"
    dwpk.standard_name = "2m Air Dew Point Temperature"
    dwpk.coordinates = "lon lat"

    # 0->65535 0 to 65.535
    uwnd = nc.createVariable('uwnd', np.uint16, ('time', 'lat', 'lon'),
                             fill_value=65335)
    uwnd.units = "meters per second"
    uwnd.scale_factor = 0.001
    uwnd.long_name = "U component of the wind"
    uwnd.standard_name = "U component of the wind"
    uwnd.coordinates = "lon lat"

    # 0->65535 0 to 65.535
    vwnd = nc.createVariable('vwnd', np.uint16, ('time', 'lat', 'lon'),
                             fill_value=65535)
    vwnd.units = "meters per second"
    vwnd.scale_factor = 0.001
    vwnd.long_name = "V component of the wind"
    vwnd.standard_name = "V component of the wind"
    vwnd.coordinates = "lon lat"

    # 0->65535  0 to 655.35
    p01m = nc.createVariable('p01m', np.uint16, ('time', 'lat', 'lon'),
                             fill_value=65535)
    p01m.units = 'mm'
    p01m.scale_factor = 0.01
    p01m.long_name = 'Precipitation'
    p01m.standard_name = 'Precipitation'
    p01m.coordinates = "lon lat"
    p01m.description = "Precipitation accumulation for the hour valid time"

    nc.close()


def compute_hasdata(year):
    """Compute the has_data grid"""
    nc = ncopen(iemre.get_hourly_ncname(year), 'a', timeout=300)
    czs = CachingZonalStats(iemre.AFFINE)
    pgconn = get_dbconn('postgis')
    states = gpd.GeoDataFrame.from_postgis("""
    SELECT the_geom, state_abbr from states
    where state_abbr not in ('AK', 'HI')
    """, pgconn, index_col='state_abbr', geom_col='the_geom')
    data = np.flipud(nc.variables['hasdata'][:, :])
    czs.gen_stats(data, states['the_geom'])
    for nav in czs.gridnav:
        grid = np.ones((nav.ysz, nav.xsz))
        grid[nav.mask] = 0.
        jslice = slice(nav.y0, nav.y0 + nav.ysz)
        islice = slice(nav.x0, nav.x0 + nav.xsz)
        data[jslice, islice] = np.where(grid > 0, 1, data[jslice, islice])
    nc.variables['hasdata'][:, :] = np.flipud(data)
    nc.close()


def main(argv):
    """Go Main Go"""
    year = int(argv[1])
    init_year(datetime.datetime(year, 1, 1))
    compute_hasdata(year)


if __name__ == '__main__':
    main(sys.argv)
