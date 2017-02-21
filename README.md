# MapMatching
EECS 395 Assignment 2

##Installing
The following dependencies need to be installed via command line to run our script.

pip install LatLon

##Run 
python main.py

###File Hierarchy
This script runs under the assumption that the unzipped rar file (with the csv files) is within the same directory, and named 'probe_data_map_matching'. The csv files should be the named the same as the unzipped file: "Partition6467LinkData.csv" and "Partition6467ProbePoints.csv"

##Output
Map matching output is the following file:

Partition6467MatchedPoints.csv	 The subset of probe points in partion 6467 that were successfully map-matched to a link.

MatchedPoints Record Format:

	sampleID, dateTime, sourceCode, latitude, longitude, altitude, speed, heading, linkPVID, direction, distFromRef, distFromLink

		sampleID	is a unique identifier for the set of probe points that were collected from a particular phone.
		dateTime	is the date and time that the probe point was collected.
		sourceCode	is a unique identifier for the data supplier (13 = Nokia).
		latitude	is the latitude in decimal degrees.
		longitude	is the longitude in decimal degrees.
		altitude	is the altitude in meters.
		speed		is the speed in KPH.
		heading		is the heading in degrees.
		linkPVID	is the published versioned identifier for the link.
		direction	is the direction the vehicle was travelling on thelink (F = from ref node, T = towards ref node).
		distFromRef	is the distance from the reference node to the map-matched probe point location on the link in decimal meters.
		distFromLink	is the perpendicular distance from the map-matched probe point location on the link to the probe point in decimal meters.

In Terminal, the program will print the following in order:<br />
	1. The derived slope <br />
	2. The average calculated actual slope if provided in Link Data <br />
	3. The difference between the derived slope and actual slope <br />
	4. When there is a match and it indicates that the program is writing to the csv

##Resources
We referenced the following resources:

###LatLon Package
https://pypi.python.org/pypi/LatLon/1.0.2

