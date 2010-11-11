"""
Compute out the peak ASOS rainfall intensities, since we have this fancy
1 minute archive going
"""

import iemdb
import numpy
import datetime
ASOS = iemdb.connect("asos", bypass=True)
IEM = iemdb.connect("iem", bypass=True)


MAXI = [1, 5, 10, 15, 20, 30, 60, 90, 120]
MAXV = {}
MAXS = {}
MAXD = {}
for i in MAXI:
  MAXV[i] = 0
  MAXS[i] = ""
  MAXD[i] = ""

# Query out the rainfall events
acursor = ASOS.cursor()
icursor = IEM.cursor()
#icursor.execute("""SELECT day, station from summary_2003 
#  where day < '2010-09-01' and network = 'IA_ASOS' and pday > 0.2""")
# IEM Access no esta akey apriori 2004
icursor.execute("""select distinct date(valid), station from hourly_2009
    WHERE network = 'IA_ASOS' and phour > 0.05 and valid > '2009-03-01'""")
for row in icursor:
    # Now we go look for rainfall data
    acursor.execute("""SELECT valid, precip from t2009_1minute where
      valid >= %s and valid < %s + '36 hours'::interval 
      and station = %s and precip > 0  and precip < 0.3
      """, (row[0], row[0],
      row[1]))
    ts0 = datetime.datetime(row[0].year, row[0].month, row[0].day)
    data = numpy.zeros( (2160,), 'f')
    for row2 in acursor:
        ts1 = datetime.datetime(row2[0].year, row2[0].month, row2[0].day, row2[0].hour, row2[0].minute)
        offset = ((ts1 - ts0).days * 1440) + ((ts1 - ts0).seconds / 60)
        data[offset] = row2[1]
    # Shortcut
    if max(data) < 0.05:
        continue
    # Now we dance
    for i in MAXI:
        for k in range(0,2160-i+1):
            s = sum( data[k:k+i] )
            if s > MAXV[i]:
                MAXV[i] = s
                MAXS[i] = row[1]
                MAXD[i] = ts0 + datetime.timedelta(minutes=k)
                print "NEW %3s INT Station: %s Time: %s Val: %.2f" % (i,
                  MAXS[i], MAXD[i], MAXV[i]) 

print "FINAL"
for i in MAXI:
  print "%s,%s,%s,%.2f" % (i, MAXS[i], MAXD[i], MAXV[i])
