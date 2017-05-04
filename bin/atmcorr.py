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
import os
from atmospheric import Atmospheric
from astronomical import Astronomical
import pandas as pd
import numpy as np
import math
import time
from Py6S import *

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
    Maps inputFinder() over a feature collection
    """

    ee.Initialize()

    return fc.map(Atmcorr.inputFinder)
  
  def exportInputs(fc_with_inputs, start=False, fileName=None):
    """
    Export atmcorr inputs to .csv file; this allows batch
    processing by avoiding .getInfo() (NB. we need the 
    atmcorr inputs client-side to run the atmcorr code)
    """

    ee.Initialize()

    if fileName is None:
      fileName = 'atmcorr_'+time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())

    task = ee.batch.Export.table.toDrive(collection = fc_with_inputs,description = fileName)
  
    if start:
      task.start()
      return
    else:
      return task
  
  def handle_GEE_columns(df):
    """
    Handles special GEE column names: 'system:index' and '.geo'

    df = pandas.DataFrame (from reading GEE .csv)
    """
    
    # remove system:index column
    if 'system:index' in df:
      df.drop('system:index', axis=1, inplace=True)

    # rename '.geo' column to 'geometry'
    if '.geo' in df:
      df['geometry'] = df['.geo']
      df.drop('.geo', axis=1, inplace=True)
    
    return df
      
  def run6S(csv_path, predefined_wavelength=None, start_wavelength=None, \
    end_wavelength=None, spectral_filter=None, keepOriginal=False):
    """
    Run the full 6S radiative transfer code through the Py6S interface.
    
    example:
    $ from atmcorr import Atmcorr
    $ Atmcorr.run6S('assetIDs_with_atmcorr_inputs.csv', predefined_wavelength = 'S2A_MSI_01')
    
    PROs
    - accurate 
    - reliable

    CONs
    - very slow
    
    Processing of large image collections may require 6S emulator!
    """
    
    print('running 6S.. (this may take a while..)')
    
    # read inputs from file
    inputs = pd.read_csv(csv_path)

    # handle special GEE columns
    inputs = Atmcorr.handle_GEE_columns(inputs)
    
    t = time.time()
    
    # wavelength 
    # - predefined_wavelength = known satellite mission
    # - user-defined = any other wavelength selection, i.e: 'scalar' or '2-tuple +/ filter function'
    # prefix = column name for .csv
    if predefined_wavelength:
      wavelength = Wavelength(PredefinedWavelengths.__dict__[predefined_wavelength])
      prefix = predefined_wavelength
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
    s.geometry.month = 1 # Earth-sun distance correction is later..
    s.geometry.day = 4   # ..applied from perihelion, i.e. Jan 4th.  
    s.wavelength = wavelength
    
    # run 6S over input variables
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
    
    # keep an original copy?
    if keepOriginal:
      inputs.to_csv(csv_path+'_(original)', index=False)

    # add correction coefficients to new dataframe
    new_df = inputs
    new_df[prefix+'_6S_a'] = [x[0] for x in outputs]
    new_df[prefix+'_6S_b'] = [x[1] for x in outputs]

    # export new dataframe to .csv (i.e. append correction coeffs. to file)
    new_df.to_csv(csv_path, index=False)
