import csv
import sys
from LatLon import LatLon
import numpy as np


link_file = open('probe_data_map_matching/Partition6467LinkData.csv', 'rb')
probe_file = open('probe_data_map_matching/Partition6467ProbePoints.csv', 'rb')

link_data = csv.reader(link_file, delimiter= '\t')
probe_data = csv.reader(probe_file, delimiter= '\t')

links = []
probes = dict()

counter = 0

for row in link_data:
    r = row[0].split(',')
    link = dict()
    link['linkPVID'] = r[0]
    link['refNodeID'] = r[1]
    link['nrefNodeID'] = r[2]
    link['length'] = r[3]
    link['funcClass'] = r[4]
    link['dir'] = r[5]
    link['speedCat'] = r[6]
    link['fromRefSpeedLimit'] = r[7]
    link['toRefSpeedLimit'] = r[8]
    link['fromRefNumLanes'] = r[9]
    link['toRefNumLanes'] = r[10]
    link['multiDigitized'] = r[11]
    link['urban'] = r[12]
    link['timeZone'] = r[13]
    link['shapeInfo'] = r[14]
    link['curvatureInfo'] = r[15]
    link['slopeInfo'] = r[16]
    links.append(link)

for row in probe_data:
    if counter > 128719:
        break
        
    r = row[0].split(',')
    sample_id = r[0]
    if sample_id not in probes.keys():
        probes[sample_id] = []

    d = dict()
    d['dateTime'] = r[1]
    d['sourceCode'] = r[2]
    d['lat'] = r[3]
    d['long'] = r[4]
    d['alt'] = r[5]
    d['speed'] = r[6]
    d['heading'] = r[7]
    
    probes[sample_id].append(d)
    counter += 1


# print len(probes)
# print len(links)

for p in probes:
    closestdist = {}
    closestangle = {}
    current = probes[p]
    initial = current[0]
    last = current[len(current)-1]
    initial_coord = LatLon(float(initial['lat']), float(initial['long']))
    last_coord = LatLon(float(last['lat']), float(last['long']))
    prob_vector = initial_coord - last_coord
    angle_probe = prob_vector.heading
    if angle_probe < 0:
        angle_probe = angle_probe + 180
    avgspeed = 0
    for i in xrange(len(current)):
        avgspeed += float(current[i]['speed'])
    avgspeed = avgspeed / len(current)
    minspeed = 9999999
    minindex = 0

    for i in xrange(len(links)):
        l = links[i]
        shapeInfo = l['shapeInfo'].replace('|', '/').split('/')
        ref_coord = LatLon(float(shapeInfo[0]), float(shapeInfo[1]))
        nref_coord = LatLon(float(shapeInfo[3]), float(shapeInfo[4]))
        diff_vector = ref_coord - nref_coord
        angle_link = diff_vector.heading
        if angle_link < 0:
            angle_link = angle_link + 180
        links[i]['angle_link'] = angle_link
        # print "vectors"
        # print diff_vector, prob_vector
        # print "angles"
        # print angle_link, angle_probe

        distance = initial_coord.distance(ref_coord)
        if len(closestdist) < 50:
            closestdist[distance]= i
        else:
            if max(closestdist.keys()) > distance:
                del closestdist[max(closestdist.keys())]
                closestdist[distance] = i
    for i in closestdist:
        diff = abs(angle_probe - links[closestdist[i]]['angle_link'])
        if len(closestangle) < 25:
            closestangle[diff]= closestdist[i]
        else:
            if max(closestangle.keys()) > diff:
                del closestangle[max(closestangle.keys())]
                closestangle[diff] = closestdist[i]
    for i in closestangle:
        speeddiff = abs(avgspeed - float(links[closestangle[i]]['fromRefSpeedLimit']))
        if speeddiff < minspeed:
            minspeed = speeddiff
            minindex = closestangle[i]
    
    
    sys.exit()







    
    
    