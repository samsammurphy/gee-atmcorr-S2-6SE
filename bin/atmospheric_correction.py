"""
atmospheric_correction.py
"""

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