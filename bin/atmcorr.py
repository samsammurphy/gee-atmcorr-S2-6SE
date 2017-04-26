"""
atmcorr.py, Sam Murphy (2017-04-25)

Atmospheric correction of satellite image collections in
Google Earth Engine (GEE).

Usage
-----

> Please see the jupyter notebook for detailed usage: 
https://github.com/samsammurphy/gee-atmcorr-S2-batch

> The following is a short summary:

1) find input variables that are require for atmospheric correction
   of your Google Earth Engine collection

`Atmcorr.findInputs(fc)`
   
2) export inputs to .csv  <-- i.e. allows processing of large collections
                                   without using .getInfo() too many times
                                   and allows results to be saved for
                                   upload to fusion table

`Atmcorr.exportInputs()`

3) runs 6S emulator over csv

`Atmcorr.run6SE(csv)` <-- i.e. adds atmospheric correction parameters to
                               the csv that was exported in step (2) these 
                               parameters are used to convert from radiance 
                               (or top of atmosphere reflectance) to surface reflectance

Optionally
----------

runs Py6S (i.e. original source code) over csv

`Atmcorr.runPy6S(csv) `  <-- i.e.  this is much slower but might be useful if, e.g.
                                   i) your image collection is small (< 50 images)
                                   ii) your want to compare 6S and the 6S emulator

"""
import ee
from atmospheric import Atmospheric

ee.Initialize()

class Atmcorr:

  def __init__(self):
    self.pi = 3.141592653589793
    self.degToRad = self.pi / 180 # degress to radians
    self.radToDeg = 180 / self.pi # radians to degress
    return
  
  # trigonometric functions
  def sin(self,x):
    return ee.Number(x).sin()
  def cos(self,x):
    return ee.Number(x).cos()
  def radians(self,x):
    return ee.Number(x).multiply(self.degToRad)
  def degrees(self,x):
    return ee.Number(x).multiply(self.radToDeg)
  
  def dayOfYear(self):
    jan01 = ee.Date.fromYMD(self.date.get('year'),1,1)
    self.doy = self.date.difference(jan01,'day').toInt().add(1)
    return self.doy
  
  def solarDeclination(self):
    """
    Calculates the solar declination angle (radians)
    https://en.wikipedia.org/wiki/Position_of_the_Sun

    simple version..
    d = ee.Number(self.doy).add(10).multiply(0.017214206).cos().multiply(-23.44)

    a more accurate version used here..
    """
    N = ee.Number(self.doy).subtract(1)
    solstice = N.add(10).multiply(0.985653269)
    eccentricity = N.subtract(2).multiply(0.985653269).multiply(self.degToRad).sin().multiply(1.913679036)
    axial_tilt = ee.Number(-23.44).multiply(self.degToRad).sin()
    return solstice.add(eccentricity).multiply(self.degToRad).cos().multiply(axial_tilt).asin()
  
  def solarZenith(self):
    """
    Calculates solar zenith angle (degrees)
    https://en.wikipedia.org/wiki/Solar_zenith_angle
    """
    latitude = self.radians(self.geom.centroid().coordinates().get(1))
    doy = self.dayOfYear()
    d = self.solarDeclination()
    hourAngle = self.radians(self.date.get('hour').subtract(12).multiply(15))
    sines = self.sin(latitude).multiply(self.sin(d))
    cosines = self.cos(latitude).multiply(self.cos(d)).multiply(self.cos(hourAngle))
    self.solar_z = sines.add(cosines).acos()
    return self.solar_z.multiply(self.radToDeg)
  
  def inputFinder(self,feature):
    self.geom = feature.geometry().centroid()
    self.date = ee.Date(feature.get('date'))
    inputVars = ee.Dictionary({
      'H2O':Atmospheric.water(self.geom,self.date),
      'O3':Atmospheric.ozone(self.geom,self.date),
      'AOT':Atmospheric.aerosol(self.geom,self.date),
      'solar_z':self.solarZenith()     
    })
    return ee.Feature(self.geom,inputVars).copyProperties(feature)
  
  def findInputs(self, fc):
    self.fc = fc
    self.fc_with_inputs = fc.map(self.inputFinder)
    return self.fc_with_inputs # return for debuggong only
  
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

# debugging
img = ee.Image('COPERNICUS/S2/20170115T112411_20170115T112412_T29SLV')
print('MEAN_SOLAR_ZENITH_ANGLE',img.get('MEAN_SOLAR_ZENITH_ANGLE').getInfo())

ac = Atmcorr()
inputs = ac.findInputs(fc).getInfo()
  
print('Solar zenith at geom: ',inputs['features'][0]['properties']['solar_z'])