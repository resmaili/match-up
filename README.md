# AERONET MATCH-UP CODE
## Description
This program reads in satellite data and performs a ground match-up.
This code was written in my spare time, use at your own risk.

## Getting Started
### Prerequisites
This is a python script, so you will need python on your computer to run this code. If you don't know where to start, I suggest installing [Anaconda Python](https://anaconda.org/anaconda/python).

## Running

### Step 1: Configure paths
You will need to update the following paths in both main.py and support\_functions.py to reflect where the code (project\_path), satellite data (sat\_path), ground_data (gnd\_path), geolocation files (geolocation\_luts; Also see [a note on geolocation files](#A-note-on-geolocation-files)), and the configuration file with the match-up location names and coordinates (config\_path).

In support\_functions.py:

```
sat_path = "sat/"
ground_path = "gnd/"
geoloc_path = "geolocation_luts/"
config_path = "config_files/"
```

In main.py:

```
project_path = "/"
output_path = project_path + "results/"
```

Also update the dates to process (It's crude: this is work in progress!):
```
dates = [ '2018188']
```
#### A note on geolocation files
GOES products follow a scaled fixed grid scheme. Because the data are geostationary, they are mapped to the same point regardless of the time of the day. Thus, rather than perform the calculation each time, it is common to [create geolocation a look-up table (LUT)](https://github.com/resmaili/geolocation) is made once for a product and re-used thereafter to speed up processessing. Note that if you are using VIIRS or MODIS based AOD retrievals, the data is NOT stationary. However, the latitude and longitude values are included in the file itself.

### Step 2: Download the data
* Satellite: [Comprehensive Large Array-data Stewardship System (CLASS)](https://www.class.noaa.gov/).
* Ground: [AERONET (AErosol RObotic NETwork) project](https://aeronet.gsfc.nasa.gov)

### Step 3: Run the script
You can run the script via the Anaconda Prompt or terminal by typing:
```
python main.py
```

### Step 4: Check the Output

## Author
* **Rebekah Bradley Esmaili** [bekah@umd.edu](mailto:bekah@umd.edu)

## More Information

* [Comprehensive Large Array-data Stewardship System (CLASS)](https://www.class.noaa.gov/).
