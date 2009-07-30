# Generate a map of Yearly Precipitation

import sys, os
sys.path.append("../lib/")
import iemplot

import mx.DateTime
now = mx.DateTime.now()

from pyIEM import iemdb, stationTable
st = stationTable.stationTable("/mesonet/TABLES/coopClimate.stns")
st.sts["IA0200"]["lon"] = -93.4
st.sts["IA5992"]["lat"] = 41.65
i = iemdb.iemdb()
coop = i['coop']

def runYear(year):
  # Grab the data
  sql = """SELECT stationid, sum(precip) as total
           from alldata WHERE year = %s GROUP by stationid""" % (year,)

  lats = []
  lons = []
  vals = []
  labels = []
  rs = coop.query(sql).dictresult()
  for i in range(len(rs)):
    if rs[i]['total'] < 10: # Arb Threshold
      continue
    id = rs[i]['stationid'].upper()
    if not st.sts.has_key(id):
      continue
    labels.append( id[2:] )
    lats.append( st.sts[id]['lat'] )
    lons.append( st.sts[id]['lon'] )
    vals.append( rs[i]['total'] )

    #---------- Plot the points

  cfg = {
     'wkColorMap': 'gsltod',
     '_format'   : '%.2f',
     '_labels'   : labels,
     '_title'    : "Total Precipitation [inch] (%s)" % (year,),
  }

  iemplot.simple_valplot(lons, lats, vals, cfg)

  os.system("convert -depth 8 -colors 128 -trim -border 5 -bordercolor '#fff' -resize 900x700 +repage -density 120 tmp.ps temp.png")
  os.system("/home/ldm/bin/pqinsert -p 'plot a %s00000000 bogus summary/total_precip.png png' temp.png" % (year,))
  os.remove("temp.png")
  os.remove("tmp.ps")

for i in range(1893,2009):
  runYear(i)
