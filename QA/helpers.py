import os
def getRelease(cycle):
    cyc = cycle.replace('.','_')
    if cyc[:-2] != '_X': cyc += '_X'
    cmd = 'scramv1 list CMSSW | grep '+cyc+'_2 |grep -v "/afs/cern.ch/" | tail -1 '
    pipe = os.popen(cmd)
    res = pipe.readlines()
    pipe.close()
    if len(res) != 1:
        print "ERROR: wrong result from pipe:", res
        return None
    rel = res[0].split()[1].strip()
    return rel

def getReleasePath(rel):
    cmd = 'scramv1 list CMSSW ' + rel +' | grep /'+rel+' | tail -1 '
    pipe = os.popen(cmd)
    res = pipe.readlines()
    pipe.close()
    if len(res) != 1:
        print "ERROR: wrong result from pipe:", res
        return None

    relpath = res[0].split()[1].strip()
    return relpath
    
def newPrefPart(part):
    x,y = part.split("of",1)
    x1  = int(x)
    y1  = int(y)+1
    y2  = int(y1/2)
    xpart = "1of2"
    if x1>y2: xpart = "2of2"
    return xpart

def getStamp(rel):
    import re, datetime

    wkdy = ['mon','tue','wed','thu','fri','sat','sun']
    cand, date = re.search(r'(\w+)_(\d{4}-\d{2}-\d{2}-\d{4})', rel).groups()
    y,m,d,h = date.split('-')
    weekday = datetime.date(int(y), int(m), int(d)).weekday()
    stamp = wkdy[weekday] +'-' + str(h)[:2]
    cyc = cand.replace('CMSSW_','').replace('_','.')[:-2]
    
    return cyc, wkdy[weekday], stamp
