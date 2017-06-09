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
import math

def atmospheric_correction(rad, cc):
  """
  surface reflectance from at-sensor radiance and atmospheric correction coefficients 
  """
  
  for bandName in sorted(cc.keys()):
        
    radiance = rad.select(bandName)
    a = cc[bandName][0]
    b = cc[bandName][1]
    
    SR = radiance.select(bandName).subtract(a).divide(b)
    
    try:
      surface_reflectance
    except NameError:
      surface_reflectance = SR
    else:
      surface_reflectance = surface_reflectance.addBands(SR)
  
  return surface_reflectance   

def radiance_from_TOA(toa, feature):
    """
    At-sensor radiance from top of atmosphere (apparent) reflectance
    """
    
    for bandName in feature['properties']['bandNames']:
        
      solar_irradiance = feature['properties']['solar_irradiance'][bandName]
      solar_zenith = feature['properties']['atmcorr_inputs']['solar_z']
      solar_zenith_correction = math.cos(math.radians(solar_zenith))
      day_of_year = feature['properties']['atmcorr_inputs']['doy']
      EarthSun_distance = 1 - 0.01672 * math.cos(0.9856 * (day_of_year-4))# http://physics.stackexchange.com/questions/177949/earth-sun-distance-on-a-given-day-of-the-year
      
      # conversion factor
      multiplier = solar_irradiance * solar_zenith_correction / (math.pi * EarthSun_distance**2)
      
      # at-sensor radiance
      rad = toa.select(bandName).divide(10000).multiply(multiplier)

      try:
        radiance
      except NameError:
        radiance = rad
      else:
        radiance = radiance.addBands(rad)
    
    return radiance

#--------------------------------------------------------------------------

# a place and a mission
geom = ee.Geometry.Point(-157.816222, 21.297481)
mission = 'COPERNICUS/S2'  

# image collection
ic = ee.ImageCollection(mission)\
  .filterBounds(geom)\
  .filterDate('2017-01-01','2017-06-12')\
  .filter(ee.Filter.lt('MEAN_SOLAR_ZENITH_ANGLE',75))

# 6S emulator
se = SixS_emulator(mission)

# load interpolate look up tables
se.load_iLUTs('/home/sam/git/github/gee-atmcorr-S2-batch/files/iLUTs/S2A_MSI/Continental/view_zenith_0/')

# extract atmcorr inputs as feature collection
Atmcorr_input.geom = geom  # specific target location (would use image centroid otherwise)
atmcorr_inputs = ic.map(Atmcorr_input.extractor).getInfo()
features = atmcorr_inputs['features']

# debugging
# import pickle
# pickle.dump(atmcorr_inputs, open('atmcorr_inputs.p','wb'))
# atmcorr_inputs = pickle.load(open('atmcorr_inputs.p','rb'))
# features = atmcorr_inputs['features']
# feature = features[0]

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