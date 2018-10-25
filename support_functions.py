#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Description
    
@Version: 1.0

@author: Rebekah Bradley Esmaili
@email: bekah@umd.edu
"""

from netCDF4 import Dataset
import numpy as np
import datetime as dt
from glob import glob
from os.path import exists
import csv

# Define input paths
sat_path = "sat/"
ground_path = "gnd/"
geoloc_path = "geolocation_luts/"
config_path = "config_files/"


missing = -999.0
#----------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------#
def get_coordinates(input_type):
	# Need to create geolocation input file first!
    file_latlon = geoloc_path + "latlon_" + input_type + ".nc"

    if exists(file_latlon):
        file_id_coords = Dataset(file_latlon, mode='r')
        latitude = file_id_coords.variables['Latitude'][:]
        longitude = file_id_coords.variables['Longitude'][:]
        
	else:
		"Error: No geolocation file found. Quitting."
		quit()
            
    return latitude, longitude

#----------------------------------------------------------------------------------------
# Read Aeronet --------------------------------------------------------------------------
def readAeronetConfig():
    filepath = config_path + 'aeronet_stations.csv'
    with open(filepath) as csvDataFile:
        csvReader = csv.reader(csvDataFile)
        next(csvReader, None)
        sitenames=[]
        site_lat=[]
        site_lon=[]
        for row in csvReader:
            sitenames.append(row[0])
            site_lat.append(float(row[1]))
            site_lon.append(float(row[2]))
            
    return sitenames, site_lat, site_lon

def readAeronet(sitenames, date):
    site_count = len(sitenames)
    for sitenum, sitename in enumerate(sitenames):
    
        filename = ground_path + sitename + "/aeronet_" + sitename + "_" + date + ".csv"
        if exists(filename):
            with open(filename) as csvDataFile:
                csvReader = csv.reader(csvDataFile)
                row_count = sum(1 for row in csvReader)
                csvReader = csv.reader(csvDataFile)
                dims = (site_count, row_count)
                aeronet_time = np.empty(dims, int)
                aeronet_aot_500 = np.empty(dims, float)
                aeronet_sza = np.empty(dims, float)
                
            with open(filename) as csvDataFile:
                csvReader = csv.reader(csvDataFile)
                rownum=0
                for row in csvReader:
                
                    aod500 = returnFloat(row[12], missing)
                    if (aod500 == missing):
                        continue
                        
                    aeronet_aot_500[sitenum, rownum] = aod500
                    aeronet_time[sitenum, rownum] = returnStrTime(row[1])
                    aeronet_sza[sitenum, rownum] = returnFloat(row[44], missing)
                    rownum = rownum+1
                    
    return aeronet_time, aeronet_aot_500, aeronet_sza
    
#----------------------------------------------------------------------------------------
#Read Sat-------------------------------------------------------------------------------
def getSatFilenames(date, time):        
    searchForFiles = sat_path + '/*_s' + date + time + '*.nc'
    
    filenames = []
    for filename in glob(searchForFiles):
        filenames.append(filename)
        
    return filenames
  
#----------------------------------------------------------------------------------------
#Matchup-------------------------------------------------------------------------------
def matchup_temporal(time, time_array, matchup_max_time_mins=15):
    time_array_int = time_array.astype(int)
    time_int = int(time)
    time_array_int = [np.abs(x - time_int) for x in time_array_int]
    index = np.argmin(time_array_int)
    
    print("matchup_temporal ", time_int, time_array[index], time_array_int[index] )
    
    if (time_array_int[index] <= matchup_max_time_mins):
        return index
    else:
        return -1
 
def matchup_spatial(latitude, longitude, site_lat, site_lon, matchup_radius_km=25.0):
    # Find index for pixels within matchup_radius_km around ground site    
    distance_matrix = np.zeros(latitude.shape)

    distance_matrix = np.sqrt( (np.array(latitude) - site_lat)**2 + (np.array(longitude) - site_lon)**2 )
    distance_matrix[ distance_matrix > 1.0 ] = 0.0
    
    if np.sum(distance_matrix) == 0:
        return [-1, -1]

    # Replace angle distance with km distance
    distance_matrix[ distance_matrix > 0.0 ] = haversine(site_lat, site_lon, latitude[ distance_matrix > 0.0 ], longitude[ distance_matrix > 0.0 ])
    distance_matrix[ distance_matrix > matchup_radius_km ] = 0.0

    if np.sum(distance_matrix) == 0:
        return [-1, -1]
    
    # Get indices of the match-up
    return np.where(distance_matrix > 0)

def haversine(deglat1, deglon1, deglat2, deglon2):
    lat1=deglat1*np.pi/180.0
    lat2=deglat2*np.pi/180.0
    
    long1=deglon1*np.pi/180.0
    long2=deglon2*np.pi/180.0
      
    a = np.sin(0.5 * (lat2 - lat1))
    b = np.sin(0.5 * (long2 - long1))
    
    dist = 12742.0 * np.arcsin(np.sqrt(a * a + np.cos(lat1) * np.cos(lat2) * b * b))
    
    return dist
#---------------------------------------------------------------------------------------
#Output-------------------------------------------------------------------------------    
def writeSatToHDF(hf, channel, station, ftime, matchup_var, matchup_length):
    # Create group station/time (15 min intervals)
    g0 = hf.require_group(station)

    time15 = round_to_15(ftime);
    group_name = format(time15, '05.2f')
    g1 = g0.require_group(group_name)

    # Write G16 data to HDF5
    if channel in g1:
        # Append match-ups to HDF
        g1[channel].resize((g1[channel].shape[0] + matchup_length), axis = 0)
        g1[channel][-matchup_length:] = matchup_var
        
    else:
        # Create dataset in HDF
        d1 = g1.create_dataset(channel, data=matchup_var, maxshape=(None,), chunks=(matchup_length,), compression="gzip", dtype='f', fillvalue=missing)
        d1.attrs['long_name'] = "ABI L1b Radiances for Channel " + channel[1:3]
        d1.attrs['standard_name'] = "toa_outgoing_radiance_per_unit_wavelength"
        d1.attrs['units'] = "W m-2 sr-1 um-1"

def writeGndToHDF(hf, channel, station, ftime, tmp_aod, tmp_sza, matchup_length):
    # Create group station/time (15 min intervals)
    g0 = hf.require_group(station)

    time15 = round_to_15(ftime);
    group_name = format(time15, '05.2f')
    g1 = g0.require_group(group_name)

    # Write AERONET data to HDF5
    if 'AOD500' in g1:
        g1['AOD500'].resize((g1['AOD500'].shape[0] + matchup_length), axis = 0)
        g1['AOD500'][-matchup_length:] = tmp_aod

        g1['SZA'].resize((g1['SZA'].shape[0] + matchup_length), axis = 0)
        g1['SZA'][-matchup_length:] = tmp_sza
         
    else:
        d1 = g1.create_dataset('AOD500', data=tmp_aod, maxshape=(None,), chunks=(matchup_length,), compression="gzip", dtype='f', fillvalue=missing)
        d1.attrs['long_name'] = "Aerosol Optical Depth (AOD) SURFRAD Level 1.5"
        d1.attrs['standard_name'] = "AOD_550"
        d1.attrs['units'] = "none"
         
        d2 = g1.create_dataset('SZA', data=tmp_sza, maxshape=(None,), chunks=(matchup_length,), compression="gzip", dtype='f', fillvalue=missing)
        d2.attrs['long_name'] = "Solar Zenith Angle for 1020nm Channel"
        d2.attrs['standard_name'] = "solar_zenith_angle_for_1020nm _scan"
        d2.attrs['units'] = "degrees"    
        
#---------------------------------------------------------------------------------------
#Helpers ------------------------------------------------------------------------------- 
def round_to_15(str_x):
    fhr = float(str_x[0:2])
    fmin = float(str_x[2:4])/60.0
    x = fhr + fmin
    return int(np.round(x/0.25))*0.25
    
def returnFloat(x, missing):
    #if isinstance(x, float) or isinstance(x, int):
    if (x == "N/A"):
        return missing
    elif (float(x) > 5 or float(x) < -0.5):
        return missing
    else:
        return float(x)
        
def returnJulDate(x):
    fmt = '%d:%m:%Y'
    tt = dt.datetime.strptime(x, fmt).timetuple()
    return int('%d%03d' % (tt.tm_year, tt.tm_yday))
    
def returnStrTime(x):
    fmt = '%H:%M:%S'
    tt = dt.datetime.strptime(x, fmt).timetuple()
    return tt.tm_hour*100 + tt.tm_min


    