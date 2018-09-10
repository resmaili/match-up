#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Description: 
-- Perform match-ups between AERONET site and G16 CONUS AOD. Can be modified for other GEO inputs.
-- To download G16 AOD products, visit www.class.noaa.gov.
-- AERONET is downloaded and formatted for input.
-- Look-up tables for the fixed grid ABI are generated/saved for faster processing.
-- Match-us are performed within a specified radius and time of the aeronet station.
-- Results are saved to a CSV file.
    
@author: Rebekah Bradley Esmaili
@email: bekah@umd.edu
"""

from netCDF4 import Dataset
from os import system
from os.path import basename
import sys
import timeit

# Parameters -------------------
dates = [ '2018188']

project_path = "/"
output_path = project_path + "results/"

# Select paramters, sites to process
matchup_radius_km = 5.0
matchup_max_time_mins = 15
missing = -999.0

# Begin ----------
start = timeit.default_timer()
sys.path.append(project_path)
import support_functions as sf

# Get lat/lon list
sitenames, site_lat, site_lon = sf.readAeronetConfig()

# Open geolocation file
latitude, longitude = sf.get_coordinates('L2_conus')

#Get spatial match-ups
arraylen = len(sitenames)
matchup_index[None] * arraylen

#Yes, this needs to be cleaned up... could also be saved to CSV
for sitenum, station in enumerate(sitenames):
    matchup_index[sitenum] = sf.matchup_spatial(latitude, longitude, site_lat[sitenum], site_lon[sitenum], matchup_radius_km=matchup_radius_km)

# No longer needed, clear from memory
del latitude, longitude

# Create new HDF file
with open(output_path + 'match_ups.csv','a') as fd:
	writer = csv.writer(f)
	for date in dates:
	   # Import Aeronet station data for the date, re-format fields
	   aeronet_time, aeronet_aot_500, aeronet_sza = sf.readAeronet(sitenames, date)      

	   for hh in range(0, 23):
		   for mm in range(0, 59):
	   
			   # Search for G16 data at given time
			   time = str(hh) + str(mm)
			   filename = sf.getSatFilenames(date, time)
			   if (len(filenames) < 1):
				   continue
			
			   for sitenum, station in enumerate(sitenames):
				   # Check spatial match-ups w/site
				   if (np.sum(matchup_index) < 0 ):
					   continue
		   
				   # Get/check temporal match-ups w/site
				   time_index = sf.matchup_temporal(time, aeronet_time[sitenum,:], matchup_max_time_mins=matchup_max_time_mins)
				   if (time_index == -1):
					   continue
				   
				   # Open satellite dataset
				   print("Match-up for: " + station[sitenum] + ' || ' + basename(filename))
				   file_id = Dataset(filename, mode='r')
			   
				   var = file_id.variables['AOD']
				   sat_aod = np.mean(var[matchup_index[sitenum])
			   
				   index = [sitenum, time_index]
				   gnd_time = aeronet_time[index]
				   gnd_aod = aeronet_aot_500[index]
				   sza = aeronet_sza[index]
				   
				   writer.writerow(station, gnd_time, gnd_aod, sat_aod, sza)
				   
print("Done.")
stop = timeit.default_timer()
print("Run time:" + str((stop - start)/60) + " minutes.")
