"""
atmcorr.py, Sam Murphy (2017-04-25)

Atmospheric correction of satellite image collections in
Google Earth Engine (GEE).

Usage
-----

> Please see the jupyter notebook for detailed usage: 
https://github.com/samsammurphy/gee-atmcorr-S2-batch

> The following is a shorthand version:

1) find input variables for atmospheric correction using GEE

`Atmcorr.findInputs(fc)`
   
2) export inputs to .csv  <-- i.e. allows processing of large collections
                                   without using .getInfo() too many times
                                   and allows results to be saved for
                                   upload to fusion table

`Atmcorr.exportInputs()`

3) runs 6S emulator over csv

`Atmcorr.run6SE(csv)` <-- i.e. adds atmospheric correction parameters to
                               the csv. these parameters are used to 
                               convert from radiance (or top of atmosphere
                               reflectance) to surface reflectance

bonus) runs Py6S (i.e. original source code) over csv

`Atmcorr.runPy6S(csv) `  <-- i.e. you can optional run 6S (through Py6S). this
                                   is much slower but might be useful, e.g., if
                                   i) your image collection is small (< 50 images)
                                   ii) your want to compare 6S and the 6S emulator

"""
import ee
from atmospheric import Atmospheric

ee.Initialize()

class Atmcorr:

  def __init__(self):
    self.pi = 3.141592653589793
    self.degToRad = self.pi / 180
    self.radToDeg = 180 / self.pi
    #debugging..
    self.geom = ee.Geometry.Point(0,0)
    self.date = ee.Date('2017-12-21')
    return
  
  def solarZenith(self):
    """
    Calculates solar zenith angle (degrees).
    """
    # latitude of target (radians)
    lat = ee.Number(self.geom.centroid().coordinates().get(1)).multiply(self.degToRad)
    # day of year
    jan01 = ee.Date.fromYMD(self.date.get('year'),1,1)
    doy = self.date.difference(jan01,'day').toInt().add(1)
    # solar declination angle (radians)
    d = ee.Number(284).add(doy).divide(36.25).multiply(2*self.pi).sin()\
    .multiply(23.45).multiply(self.degToRad)
    # hour angle (radians)
    h = self.date.get('hour').subtract(12).multiply(15).multiply(self.degToRad)
    # solar zentih angle (radians)
    #solar_z_rad = math.sin(lat)*math.sin(d) + math.cos(lat)*math.cos(d)*math.cos(h)
    
    # solar zenith angle (degrees)
    return d.multiply(self.radToDeg)#solar_z_rad.multiply(180).divide(self.pi)
  
  def inputFinder(self,feature):
    self.geom = feature.geometry().centroid()
    self.date = ee.Date(feature.get('date'))
    inputVars = ee.Dictionary({
      'H2O':Atmospheric.water(self.geom,self.date),
      'O3':Atmospheric.ozone(self.geom,self.date),
      'AOT':Atmospheric.aerosol(self.geom,self.date),
    })
    return ee.Feature(self.geom,inputVars).copyProperties(feature)
  
  def findInputs(self, fc):
    self.fc = fc
    self.fc_with_inputs = fc.map(self.inputFinder)
    return
  
  def exportInputs(self):
    ee.batch.Export.table.toDrive(collection = self.fc_with_inputs,\
                                  description = 'exporting atmcorr inputs to csv..',\
                                  fileNamePrefix = 'atmcorr'
                                  ).start()
    return

fc = ee.FeatureCollection(ee.Feature(ee.Geometry.Point(-10.811, 35.353),ee.Dictionary({'landcover_type':'water', 
  'assetID':'COPERNICUS/S2/20170115T112411_20170115T112412_T29SLV', 
  'valid': 1,
  'cloud_cover': 0.0, 
  'date': ee.Date(1484479452457)})))


ac = Atmcorr()
  
print(ac.solarZenith().getInfo())