import csv
import sys
from LatLon import LatLon
import numpy as np
import math

#input data files
link_file = open('probe_data_map_matching/Partition6467LinkData.csv', 'rb')
probe_file = open('probe_data_map_matching/Partition6467ProbePoints.csv', 'rb')

link_data = csv.reader(link_file, delimiter= '\t')
probe_data = csv.reader(probe_file, delimiter= '\t')

links = []
probes = dict()

counter = 0

#function that converts LatLon points with altitude to cartesian x,y,z coords
def cartesian(latitude,longitude, elevation):
    R = 6378137.0 + elevation  # relative to centre of the earth
    X = R * math.cos(longitude) * math.sin(latitude)
    Y = R * math.sin(longitude) * math.sin(latitude)
    Z = R * math.cos(latitude)
    return X, Y, Z
 
#function that takes two points (x1, y1) and (x2, y2) that define a vector, and find the perp distance to point (x0, y0): all in cartesian coords   
def perpDistance(x1, y1, x2, y2, x0, y0):
    distance = abs(((y2-y1)*x0 - (x2-x1)*y0 + x2*y1 - y2*x1))/ (math.sqrt((y2 - y1)**2 + (x2 -x1)**2))
    return distance

#function that returns euclidean distance between two points: must be in cartesian coords
def euclidean_distance(x1, y1, x2, y2):
    distance = math.sqrt(((x1-x2)**2) + ((y1-y2)**2))
    return distance
    
#populating link data
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

#populating probe data, uncomment lines 44 and 45 if want ALL probes to load
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

for p in probes:
    closestdist = {}
    closestangle = {}
    current = probes[p]
    initial = current[0]
    last = current[len(current)-1]
    #first point in sequence
    initial_coord = LatLon(float(initial['lat']), float(initial['long']))
    #last point in sequence
    last_coord = LatLon(float(last['lat']), float(last['long']))
    #vectorize probe sequence
    prob_vector = initial_coord - last_coord
    angle_probe = prob_vector.heading
    
    #convert all angles to positive domain
    if angle_probe < 0:
        angle_probe = angle_probe + 180
    
    #find average speed across the probe sequence 
    avgspeed = 0
    for i in xrange(len(current)):
        avgspeed += float(current[i]['speed'])
    avgspeed = avgspeed / len(current)
    minspeed = 9999999
    minindex = 0
    angle_of_min = 0

    for i in xrange(len(links)):
        l = links[i]
        shapeInfo = l['shapeInfo'].replace('|', '/').split('/')
        #ref and nref latlong coords
        ref_coord = LatLon(float(shapeInfo[0]), float(shapeInfo[1]))
        nref_coord = LatLon(float(shapeInfo[3]), float(shapeInfo[4]))
        
        #vectorize link
        diff_vector = ref_coord - nref_coord
        angle_link = diff_vector.heading
        
        #convert all angles to the positive domain 
        if angle_link < 0:
            angle_link = angle_link + 180
        links[i]['angle_link'] = angle_link

        #find distance between starting points - maintain list of 20 closest
        distance = initial_coord.distance(ref_coord)
        if len(closestdist) < 20:
            closestdist[distance]= i
        else:
            if max(closestdist.keys()) > distance:
                del closestdist[max(closestdist.keys())]
                closestdist[distance] = i
    
    #find difference in angles - maintain filter to 5 closest
    for i in closestdist:
        diff = abs(angle_probe - links[closestdist[i]]['angle_link'])
        if len(closestangle) < 5:
            closestangle[diff]= closestdist[i]
        else:
            if max(closestangle.keys()) > diff:
                del closestangle[max(closestangle.keys())]
                closestangle[diff] = closestdist[i]
    
    #find link that has closest speed limit 
    for i in closestangle:
        speeddiff = abs(avgspeed - float(links[closestangle[i]]['fromRefSpeedLimit']))
        if speeddiff < minspeed:
            minspeed = speeddiff
            minindex = closestangle[i]
            angle_of_min = i

    #derive slope based on probe sequence - convert to cartesian and 
    initial_lat, initial_lon, final_elevation  = cartesian(float(initial['lat']),float(initial['long']), float(initial['alt']))
    final_lat, final_lon, final_elevation  = cartesian(float(last['lat']),float(last['long']), float(last['alt']))
    #run
    xdistance = math.sqrt(((final_lon - initial_lon)**2) + ((final_lat - initial_lat)**2))
    #rise
    yelevation = float(initial['alt']) - float(last['alt'])
    slope = math.degrees(math.atan(yelevation/xdistance))
    print "Derived slope: " + str(slope)

    chosen_link = links[minindex]
    #find given slope from csv - avg across slope info
    if chosen_link['slopeInfo']:
        slopeInfo = chosen_link['slopeInfo'].replace('|', '/').split('/')
        slope_sum = 0
        slope_counter = 0.0

        for i in xrange(1, len(slopeInfo), 2):
            temp = float(slopeInfo[i])
            #convert to positive domain
            if temp < 0:
                temp = temp + 180
            slope_sum += temp
            counter += 1
        actual_slope = slope_sum/counter
        print "Actual slope: " + str(actual_slope)
        print "Difference in slopes: " + str(abs(actual_slope - slope))
    else:
        print "Slope info was not provided for this road link"


    #####thresholding to see if good match/write in csv
    chosen_spdiff = minspeed
    chosen_angdiff = angle_of_min
    chosen_distdiff = 0
    
    for key, val in closestdist.iteritems():
        if val == minindex:
            chosen_distdiff = key
            
    #criteria thresholds
    speed_threshold = 25.0
    angle_threshold = 8.0
    distance_threshold = 1.5
    
    #matched link within threshold limits
    if chosen_spdiff < speed_threshold and chosen_angdiff < angle_threshold and chosen_distdiff < distance_threshold:
        print "we have a match! Writing to csv..."
        with open('Partition6467MatchedPoints.csv', 'a') as output:
            writer = csv.writer(output, delimiter=',')
            data = []
            linkPVID = chosen_link['linkPVID']
            link_shape = chosen_link['shapeInfo'].replace('|', '/').split('/')
            link_ref = LatLon(float(link_shape[0]), float(link_shape[1]))
            link_nref = LatLon(float(link_shape[3]), float(link_shape[4]))
        
            current_probe = probes[p]
            for point in current_probe:
                row = []
                row.append(p)
                row.append(point['dateTime'])
                row.append(point['sourceCode'])
                row.append(point['lat'])
                row.append(point['long'])
                row.append(point['alt'])
                row.append(point['speed'])
                row.append(point['heading'])
                row.append(linkPVID)
            
            
                ##calculating direction
                p_angle = point['heading']
                l_angle = chosen_link['angle_link']
                direction = str()

                if p_angle < 180:
                    if l_angle > 180:
                        direction = 'T'
                    else:
                        direction = 'F'
                else:
                    if l_angle > 180:
                        direction = 'F'
                    else:
                        direction = 'T'
                row.append(direction)
                
                ##calculating distance
                ref_elev0 = ''
                if len(chosen_link['slopeInfo']) > 2:
                    shapeInfo = chosen_link['shapeInfo'].replace('|', '/').split('/')
                    ref_elev0 = shapeInfo[2]
                
                #do not have reference elevation so cannot convert to cartesian
                if ref_elev0 == '':
                    row.append('DNE')
                else:
                    refx, refy, refz = cartesian(float(link_shape[0]),float(link_shape[1]), float(ref_elev0))
                    pointx, pointy, pointz = cartesian(float(point['lat']), float(point['long']), float(point['alt']))
                    distance_ref = euclidean_distance(refx, refy, pointx, pointy)
                    row.append(distance_ref)
            
                #calculating perpendicular distance if info for ref and nref        
                ref_elev = ''
                nref_elev = ''
                if len(chosen_link['slopeInfo']) > 5:
                    shapeInfo = chosen_link['shapeInfo'].replace('|', '/').split('/')
                    ref_elev = shapeInfo[2]
                    nref_elev = shapeInfo[len(shapeInfo)-1]
                
                #elev info not provided so cannot convert to cartesian for perp distance
                if ref_elev == '' or nref_elev == '':
                    row.append('DNE')
                else:
                    refx, refy, refz = cartesian(float(link_shape[0]),float(link_shape[1]), float(ref_elev))
                    nrefx, nrefy, nrefz = cartesian(float(link_shape[2]),float(link_shape[3]), float(nref_elev))
                    pointx, pointy, pointz = cartesian(float(point['lat']), float(point['long']), float(point['alt']))
                    perp_distance = perpDistance(refx, refy, nrefx, nrefy, pointx, pointy)
                    row.append(perp_distance)
                #append each probe sequence to data dump
                data.append(row)
            #write to csv
            writer.writerows(data)    





    
    
    