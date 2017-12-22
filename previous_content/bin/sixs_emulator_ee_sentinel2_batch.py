"""
sixs_emulator_ee_sentinel2_batch.py
"""

import os
import glob
import pickle
import math
import time

class SixS_emulator():
  """
  6S emulator

  Atmospheric correction of satellite imagery.

  Input:  > solar zenith
          > atmospheric variables
            - water vapour
            - ozone
            - aerosol optical thickness
          > target altitude
          > day of year
  
  Output: > correction coefficients (a, b)

  surface_reflectance = a * at_sensor_radiance + b
  """

  def __init__(self, mission):
    
    self.mission = mission
    self.emulation_start_time = time.strftime("%c")
    
  def load_iLUTs(self, path):
    
    if path:
      self.iLUTpath = path
    
    # Py6S to Earth Engine Sentinel 2 band name switch
    ee_sentinel2_bandNames = {
      '01':'B1',
      '02':'B2',
      '03':'B3',
      '04':'B4',
      '05':'B5',
      '06':'B6',
      '07':'B7',
      '08':'B8',
      '09':'B8A',
      '10':'B9',
      '11':'B10',
      '12':'B11',
      '13':'B12',
    }
      
    try:
      iLUTs = {}
      filepaths = glob.glob(self.iLUTpath+'*.ilut')
      for f in filepaths:
        key = os.path.basename(f).split('.')[0][-2:]
        if self.mission == 'COPERNICUS/S2':
          key = ee_sentinel2_bandNames[key]
        iLUTs[key] = pickle.load(open(f,'rb'))
    except:
      print('problem loading interpolated look up table (.ilut) files from: '+self.iLUTpath)
    
    self.iLUTs = iLUTs
  
  def run(self, inputs):
    """
    correction coefficients for each available iLUT waveband
    """
    
    if inputs:
      self.inputs = inputs

    cc = {} # correction coeffients

    for bandName in self.iLUTs.keys():
      
      ilut = self.iLUTs[bandName]
      
      perihelion = ilut(self.inputs['solar_z'],\
                        self.inputs['h2o'],\
                        self.inputs['o3'],\
                        self.inputs['aot'],\
                        self.inputs['alt'])
         
      elliptical_orbit_correction = 0.03275104*math.cos(math.radians(self.inputs['doy']/1.04137484)) + 0.96804905

      
      cc[bandName] = list(perihelion * elliptical_orbit_correction)

    return cc