"""
ee-sentinel2-batch.py

Atmospheric correction of Sentinel 2 image collection in Earth Engine
"""

import ee
ee.Initialize()

import sys
sys.path.append('/home/sam/git/github/gee-atmcorr-S2-batch/bin')
from sixs_emulator_ee_sentinel2_batch import SixS_emulator
from atmcorr_input import Atmcorr_input
from atmospheric_correction import atmospheric_correction
from radiance import radiance_from_TOA
from interpolated_LUTs import Interpolated_LUTs

# a place and a mission
geom = ee.Geometry.Point(-157.816222, 21.297481)
mission = 'COPERNICUS/S2'  

# image collection
ic = ee.ImageCollection(mission)\
  .filterBounds(geom)\
  .filterDate('2017-01-01','2017-02-01')\
  .filter(ee.Filter.lt('MEAN_SOLAR_ZENITH_ANGLE',75))

# 6S emulator
se = SixS_emulator(mission)

# load interpolate look up tables 
iLUTs = Interpolated_LUTs('COPERNICUS/S2')
# if this is first time will have to download and interpolate
iLUTs.download_LUTs()
iLUTs.interpolate_LUTs()
# otherwise can just load into the emulator from local files
se.iLUTs = iLUTs.get()

# extract atmcorr inputs as feature collection
Atmcorr_input.geom = geom  # specific target location (would use image centroid otherwise)
atmcorr_inputs = ic.map(Atmcorr_input.extractor).getInfo()
features = atmcorr_inputs['features']

# atmospherically correct image collection
ic_atmospherically_corrected = []
for feature in features:
  
  # at-sensor radiance 
  toa = ee.Image(mission+'/'+feature['properties']['imgID'])
  rad = radiance_from_TOA(toa, feature)
  
  # 6S emulator
  cc = se.run(feature['properties']['atmcorr_inputs'])

  # atmospheric correction
  SR = atmospheric_correction(rad, cc)
  ic_atmospherically_corrected.append(SR)

# Earth Engine image collection
ic_atmospherically_corrected = ee.ImageCollection(ic_atmospherically_corrected)

# test
SR = ee.Image(ic_atmospherically_corrected.first())
print(SR.reduceRegion(ee.Reducer.mean(),geom).getInfo())