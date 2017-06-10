"""
atmcorr_input.py

The Atmcorr_input class is used to extract inputs
for atmospheric correction from other datasets in 
Google Earth Engine
"""

import ee
from atmospheric import Atmospheric

class Atmcorr_input:
  
  # global elevation (kilometers)
  elevation = ee.Image('USGS/GMTED2010').divide(1000)

  # day-of-year from date
  def doy_from_date(date):
    jan01 = ee.Date.fromYMD(date.get('year'),1,1)
    doy = ee.Number(date.difference(jan01,'day')).add(1)
    return doy
  
  def extractor(image):
    
    # a time
    date = ee.Date(image.get('system:time_start'))
    
    # a place
    if not Atmcorr_input.geom:
      Atmcorr_input.geom = image.geometry().centroid()
    
    # atmospheric correction inputs
    atmcorr_inputs = ee.Dictionary({
      'solar_z':image.get('MEAN_SOLAR_ZENITH_ANGLE'),
      'h2o':Atmospheric.water(Atmcorr_input.geom,date),
      'o3':Atmospheric.ozone(Atmcorr_input.geom,date),
      'aot':Atmospheric.aerosol(Atmcorr_input.geom,date),
      'alt':Atmcorr_input.elevation.reduceRegion(\
        reducer = ee.Reducer.mean(),\
        geometry = Atmcorr_input.geom.centroid()).get('be75'),
      'doy':Atmcorr_input.doy_from_date(date)
    })
    
    # solar irradiance (to calculate at-sensor radiance from TOA)
    solar_irradiance = {
      'B1':image.get('SOLAR_IRRADIANCE_B1'),
      'B2':image.get('SOLAR_IRRADIANCE_B2'),
      'B3':image.get('SOLAR_IRRADIANCE_B3'),
      'B4':image.get('SOLAR_IRRADIANCE_B4'),
      'B5':image.get('SOLAR_IRRADIANCE_B5'),
      'B6':image.get('SOLAR_IRRADIANCE_B6'),
      'B7':image.get('SOLAR_IRRADIANCE_B7'),
      'B8':image.get('SOLAR_IRRADIANCE_B8'),
      'B8A':image.get('SOLAR_IRRADIANCE_B8A'),
      'B9':image.get('SOLAR_IRRADIANCE_B9'),
      'B10':image.get('SOLAR_IRRADIANCE_B10'),
      'B11':image.get('SOLAR_IRRADIANCE_B11'),
      'B12':image.get('SOLAR_IRRADIANCE_B12')
    }
    
    # image identifier
    imgID = image.get('system:index')
    
    # properties
    properties = {'imgID':imgID,\
                  'bandNames':['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7',\
                   'B8', 'B8A', 'B9', 'B10', 'B11', 'B12'],\
                  'atmcorr_inputs':atmcorr_inputs,\
                  'solar_irradiance':solar_irradiance}
    
    return ee.Feature(Atmcorr_input.geom,properties)