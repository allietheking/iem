"""
Extract station data from file and update any new stations we find, please
"""
from __future__ import print_function
import sys

from pyiem.util import get_dbconn, ncopen


MY_PROVIDERS = [
 "KYTC-RWIS",
 "KYMN",
 "NEDOR",
 "MesoWest",
]


def provider2network(p):
    """ Convert a MADIS network ID to one that I use, here in IEM land"""
    if p in ['KYMN']:
        return p
    if len(p) == 5 or p in ['KYTC-RWIS', 'NEDOR']:
        if p[:2] == 'IA':
            return None
        return '%s_RWIS' % (p[:2],)
    print("Unsure how to convert %s into a network" % (p,))
    return None


def clean_string(val):
    """hack"""
    return val.replace("'", ""
                       ).replace('\x00', '').replace('\xa0',  ' '
                                                     ).replace(",", "").strip()


def main(argv):
    """Go Main Go"""
    pgconn = get_dbconn('mesosite')
    mcursor = pgconn.cursor()

    fn = argv[1]
    nc = ncopen(fn)

    stations = nc.variables["stationId"][:]
    names = nc.variables["stationName"][:]
    providers = nc.variables["dataProvider"][:]
    latitudes = nc.variables["latitude"][:]
    longitudes = nc.variables["longitude"][:]
    elevations = nc.variables["elevation"][:]
    for recnum in range(len(providers)):
        thisProvider = providers[recnum].tostring().replace('\x00', '')
        if (not thisProvider.endswith('DOT') and
                thisProvider not in MY_PROVIDERS):
            continue
        stid = stations[recnum].tostring().replace('\x00', '')
        name = clean_string(names[recnum].tostring())
        if thisProvider == 'MesoWest':
            # get the network from the last portion of the name
            network = name.split()[-1]
            if network != 'VTWAC':
                continue
        else:
            network = provider2network(thisProvider)
        if network is None:
            continue
        mcursor.execute("""
            SELECT * from stations where id = %s and network = %s
        """, (stid, network))
        if mcursor.rowcount > 0:
            continue
        print('Adding network: %s station: %s %s' % (network, stid, name))
        sql = """
            INSERT into stations(id, network, synop, country, plot_name,
            name, state, elevation, online, geom, metasite)
            VALUES ('%s', '%s', 9999, 'US',
            '%s', '%s', '%s', %s, 't', 'SRID=4326;POINT(%s %s)', 'f')
        """ % (stid, network, name, name, network[:2], elevations[recnum],
               longitudes[recnum], latitudes[recnum])
        mcursor.execute(sql)
    nc.close()
    mcursor.close()
    pgconn.commit()
    pgconn.close()


if __name__ == '__main__':
    main(sys.argv)
