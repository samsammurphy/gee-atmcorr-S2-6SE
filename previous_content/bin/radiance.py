"""
radiance.py
"""

import math

def radiance_from_TOA(toa, feature):
    """
    At-sensor radiance from top of atmosphere (apparent) reflectance
    """
    
    for bandName in feature['properties']['bandNames']:
        
      solar_irradiance = feature['properties']['solar_irradiance'][bandName]
      solar_zenith = feature['properties']['atmcorr_inputs']['solar_z']
      solar_zenith_correction = math.cos(math.radians(solar_zenith))
      day_of_year = feature['properties']['atmcorr_inputs']['doy']
      EarthSun_distance = 1 - 0.01672 * math.cos(math.radians(0.9856 * (day_of_year-4)))# http://physics.stackexchange.com/questions/177949/earth-sun-distance-on-a-given-day-of-the-year
      
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