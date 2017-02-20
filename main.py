import csv
import sys
from LatLon import LatLon
import numpy as np
import math

#def perpendicular_dist(ref, nref, point):
    


link_file = open('probe_data_map_matching/Partition6467LinkData.csv', 'rb')
probe_file = open('probe_data_map_matching/Partition6467ProbePoints.csv', 'rb')

link_data = csv.reader(link_file, delimiter= '\t')
probe_data = csv.reader(probe_file, delimiter= '\t')

links = []
probes = dict()

counter = 0

def cartesian(longitude,latitude, elevation):
    R = 6378137.0 + elevation  # relative to centre of the earth
    X = R * math.cos(longitude) * math.sin(latitude)
    Y = R * math.sin(longitude) * math.sin(latitude)
    Z = R * math.cos(latitude)
    return X, Y, Z

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
    angle_of_min = 0

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
        if len(closestdist) < 20:
            closestdist[distance]= i
        else:
            if max(closestdist.keys()) > distance:
                del closestdist[max(closestdist.keys())]
                closestdist[distance] = i
                
    for i in closestdist:
        diff = abs(angle_probe - links[closestdist[i]]['angle_link'])
        if len(closestangle) < 5:
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
            angle_of_min = i

    #derive slope based on probe

    initial_lat, initial_lon, final_elevation  = cartesian(float(initial['lat']),float(initial['long']), float(initial['alt']))
    final_lat, final_lon, final_elevation  = cartesian(float(last['lat']),float(last['long']), float(last['alt']))
    xdistance = math.sqrt(((final_lon - initial_lon)**2) + ((final_lat - initial_lat)**2))
    #xdistance = initial_coord.distance(last_coord)
    yelevation = float(initial['alt']) - float(last['alt'])
    slope = math.degrees(math.atan(yelevation/xdistance))
    print "derived slope is: " + str(slope)

    chosen_link = links[minindex]
    #find given slope from csv
    if chosen_link['slopeInfo']:
        slopeInfo = chosen_link['slopeInfo'].replace('|', '/').split('/')
        slope_sum = 0
        slope_counter = 0.0

        for i in xrange(1, len(slopeInfo), 2):
            temp = float(slopeInfo[i])
            if temp < 0:
                temp = temp + 180
            slope_sum += temp
            counter += 1
        actual_slope = slope_sum/counter
        print "actual slope is: " + str(actual_slope)
    else:
        print "slope info was not provided for this road link"


    #####thresholding to see if we should match in csv
    chosen_spdiff = minspeed
    chosen_angdiff = angle_of_min
    chosen_distdiff = 0
    
    for key, val in closestdist.iteritems():
        if val == minindex:
            chosen_distdiff = key
            
    speed_threshold = 25.0
    angle_threshold = 8.0
    distance_threshold = 1.5
    
    #UNCOMMENT THIS WHEN DONE WITH TESTING
    # if chosen_spdiff < speed_threshold and chosen_angdiff < angle_threshold and chosen_distdiff < distance_threshold:
    #     print "we have a match! Writing to csv..."
        
    with open('Partition6467MatchedPoints.csv', 'w') as output:
        writer = csv.writer(output, delimiter=',')
        data = []
        linkPVID = chosen_link['linkPVID']
        link_shape = chosen_link['shapeInfo'].replace('|', '/').split('/')
        link_ref = LatLon(float(link_shape[0]), float(link_shape[1]))
        link_nref = LatLon(float(link_shape[3]), float(link_shape[4]))
        
        current_probe = probes[p]
        print "writing"
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
            point_coord = LatLon(float(point['lat']), float(point['long']))
            distance_from_ref = point_coord.distance(link_ref)*1000.0
            row.append(distance_from_ref)
            
            #calculating perpendicular distance            

            data.append(row)
       
        writer.writerows(data)
    
    print chosen_spdiff, chosen_angdiff, chosen_distdiff
    





    
    
    