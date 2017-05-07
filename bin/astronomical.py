"""
astronomical.py, Sam Murphy (2017-04-27)

Astronomical calculations (e.g. solar angles) for
processing satellite imagery through Google Earth
Engine.
"""

import ee

class Astronomical:

  pi = 3.141592653589793
  degToRad = pi / 180 # degress to radians
  radToDeg = 180 / pi # radians to degress

  def sin(x):return ee.Number(x).sin()
  def cos(x):return ee.Number(x).cos()
  def radians(x):return ee.Number(x).multiply(Astronomical.degToRad)
  def degrees(x):return ee.Number(x).multiply(Astronomical.radToDeg)

  def dayOfYear(date):
    jan01 = ee.Date.fromYMD(date.get('year'),1,1)
    doy = date.difference(jan01,'day').toInt().add(1)
    return doy

  def solarDeclination(date):
    """
    Calculates the solar declination angle (radians)
    https://en.wikipedia.org/wiki/Position_of_the_Sun

    simple version..
    d = ee.Number(.doy).add(10).multiply(0.017214206).cos().multiply(-23.44)

    a more accurate version used here..
    """
    doy = Astronomical.dayOfYear(date)
    N = ee.Number(doy).subtract(1)
    solstice = N.add(10).multiply(0.985653269)
    eccentricity = N.subtract(2).multiply(0.985653269).multiply(Astronomical.degToRad).sin().multiply(1.913679036)
    axial_tilt = ee.Number(-23.44).multiply(Astronomical.degToRad).sin()
    return solstice.add(eccentricity).multiply(Astronomical.degToRad).cos().multiply(axial_tilt).asin()

  def solarZenith(geom,date):
    """
    Calculates solar zenith angle (degrees)
    https://en.wikipedia.org/wiki/Solar_zenith_angle
    """
    latitude = Astronomical.radians(geom.centroid().coordinates().get(1))
    d = Astronomical.solarDeclination(date)
    hourAngle = Astronomical.radians(date.get('hour').subtract(12).multiply(15))
    sines = Astronomical.sin(latitude).multiply(Astronomical.sin(d))
    cosines = Astronomical.cos(latitude).multiply(Astronomical.cos(d)).multiply(Astronomical.cos(hourAngle))
    solar_z = sines.add(cosines).acos()
    return 'need to check this out'#solar_z.multiply(Astronomical.radToDeg)