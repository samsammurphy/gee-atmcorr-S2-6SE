"""
atmcorr.py, Sam Murphy (2017-04-25)

Atmospheric correction of satellite image collections in
Google Earth Engine (GEE).

Usage
-----

Please see the jupyter notebook for detailed usage: 
https://github.com/samsammurphy/gee-atmcorr-S2-batch

"""
import ee
from atmospheric import Atmospheric
from astronomical import Astronomical
import pandas as pd
import math
import time
from Py6S import *

# ee.Initialize()

class Atmcorr:
  
  def inputFinder(feature):
    """
    Finds the inputs for atmospheric correction, this
    function will be mapped over a feature collection
    """
    geom = feature.geometry().centroid()
    date = ee.Date(feature.get('date'))
    inputVars = ee.Dictionary({
      'H2O':Atmospheric.water(geom,date),
      'O3':Atmospheric.ozone(geom,date),
      'AOT':Atmospheric.aerosol(geom,date),
      'solar_z':Astronomical.solarZenith(geom,date)     
    })
    return ee.Feature(geom,inputVars).copyProperties(feature)
  
  def findInputs(fc):
    """
    Find atmcorr inputs for a given feature collection
    """
    return fc.map(Atmcorr.inputFinder)
  
  def exportInputs(fc_with_inputs):
    """
    Export atmcorr inputs to .csv file, i.e. allows batch
    processing by avoiding repeated .getInfo() calls
    """
    task = ee.batch.Export.table.toDrive(collection = fc_with_inputs,\
                                  description = 'exporting atmcorr inputs to csv..',\
                                  fileNamePrefix = 'atmcorr'
                                  )
    return task

  def run6S(csv_path):

    print('running 6S..')
    
    t = time.time()

    # initiate 6S object with constants
    s = SixS()
    s.altitudes.set_sensor_satellite_level()
    s.aero_profile = AeroProfile.__dict__['Continental']
    s.geometry = Geometry.User()
    s.geometry.view_z = 0
    s.geometry.month = 1 # Earth-sun distance correction is later
    s.geometry.day = 4   # applied from perihelion, i.e. Jan 4th.  
    
    # run 6S over input variables
    inputs = pd.read_csv(csv_path)
    outputs = []
    for i in range(inputs.shape[0]):
      
      # update 6S variables
      s.geometry.solar_z = inputs['solar_z'][i]
      s.atmos_profile = AtmosProfile.UserWaterAndOzone(inputs['H2O'][i],inputs['O3'][i])
      s.aot550 = inputs['AOT'][i]
      s.altitudes.set_target_custom_altitude(inputs['altitude'][i])
      
      """
      Py6S user interface!
      """
      #s.wavelength = spectrum
      
      # run 6S
      s.run()
      
      # solar irradiance
      Edir = s.outputs.direct_solar_irradiance             # direct solar irradiance
      Edif = s.outputs.diffuse_solar_irradiance            # diffuse solar irradiance
      E = Edir + Edif                                      # total solar irraduance
      # transmissivity
      absorb  = s.outputs.trans['global_gas'].upward       # absorption transmissivity
      scatter = s.outputs.trans['total_scattering'].upward # scattering transmissivity
      tau2 = absorb*scatter                                # transmissivity (from surface to sensor)
      # path radiance
      Lp   = s.outputs.atmospheric_intrinsic_radiance      # path radiance
      # correction coefficients for this configuration
      a = Lp
      b = (tau2*E)/math.pi
      outputs.append((Edir, Edif, tau2, Lp, a, b))

      """
      list comprehension to add outputs to df then export

      dadaa!  ?   :)
      """
   
    print('time check {}'.format(time.time()-t))

"""
Step 1
"""
# from testsites import Testsites
# testsites = Testsites()
# fc = testsites.get()
# fc_with_inputs = Atmcorr.findInputs(fc)
# task = Atmcorr.exportInputs(fc_with_inputs)
# task.start()

"""
Step 2
"""
# download the csv file locally 
Atmcorr.run6S('testsites.csv')

"""
Step 3
"""
# upload to fusion table
# use in GEE
