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
import sys
from atmospheric import Atmospheric
from astronomical import Astronomical
import pandas as pd
import numpy as np
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
    Export atmcorr inputs to .csv file. this allows 'batch'
    processing by avoiding repeated .getInfo() calls
    """
    task = ee.batch.Export.table.toDrive(collection = fc_with_inputs,\
                                  description = 'exporting atmcorr inputs to csv..',\
                                  fileNameprefix = 'atmcorr'
                                  )
    return task
    
  def run6S(csv_path, predefined=None, start_wavelength=None, end_wavelength=None, spectral_filter=None):

    print('running 6S..')
    
    t = time.time()

    # wavelength (predefined or user-defined ?)
    if predefined:
      wavelength = Wavelength(PredefinedWavelengths.__dict__[predefined])
      prefix = predefined # <-- i.e. prefix for column name for .csv (e.g. 'S2A_MSI_01')
    if start_wavelength:
      wavelength = Wavelength(start_wavelength, end_wavelength=end_wavelength, filter=spectral_filter)
      prefix = ['w',str(start_wavelength)]
      if end_wavelength:
        prefix.append(str(end_wavelength))
      if spectral_filter:
        prefix.append('f')
      prefix = '_'.join(prefix)

    # initiate 6S object with constants
    s = SixS()
    s.altitudes.set_sensor_satellite_level()
    s.aero_profile = AeroProfile.__dict__['Continental']
    s.geometry = Geometry.User()
    s.geometry.view_z = 0
    s.geometry.month = 1 # Earth-sun distance correction is later
    s.geometry.day = 4   # applied from perihelion, i.e. Jan 4th.  
    s.wavelength = wavelength
    
    # run 6S over input variables
    inputs = pd.read_csv(csv_path)
    outputs = []
    for i in range(inputs.shape[0]):
      
      # update 6S variables
      s.geometry.solar_z = inputs['solar_z'][i]
      s.atmos_profile = AtmosProfile.UserWaterAndOzone(inputs['H2O'][i],inputs['O3'][i])
      s.aot550 = inputs['AOT'][i]
      s.altitudes.set_target_custom_altitude(inputs['altitude'][i])
      
      # run 6S
      s.run()
      
      # solar irradiance
      Edir = s.outputs.direct_solar_irradiance             # direct solar irradiance
      Edif = s.outputs.diffuse_solar_irradiance            # diffuse solar irradiance
      # transmissivity
      absorb  = s.outputs.trans['global_gas'].upward       # absorption transmissivity
      scatter = s.outputs.trans['total_scattering'].upward # scattering transmissivity
      tau2 = absorb*scatter                                # transmissivity (from surface to sensor)
      # path radiance
      Lp   = s.outputs.atmospheric_intrinsic_radiance      # path radiance
      # correction coefficients for this configuration
      a = Lp
      b = (tau2*(Edir + Edif))/math.pi
      outputs.append((a, b))
    
    print('time check {}'.format(time.time()-t))
    
    # add to dataframe
    inputs[prefix+'_6S_a'] = [x[0] for x in outputs]
    inputs[prefix+'_6S_b'] = [x[1] for x in outputs]

    # export updated dataframe to .csv
    outfile = os.path.basename(csv_path)[:-4]+'_updated.csv'
    outpath = os.path.join(os.path.dirname(csv_path),outfile)
    inputs.to_csv(outpath)

# e.g.
# Atmcorr.run6S('testsites.csv', predefined = 'S2A_MSI_01')
