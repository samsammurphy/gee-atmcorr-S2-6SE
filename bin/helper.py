"""
helper.py, Sam Murphy (2017-04-24)

Helper functions for atmospheric correction in GEE

(at present) = finds image assetIDs for a collection of targets.
"""

import ee
ee.Initialize()

class FindAssets():
  """
  This class finds asset IDs for a collection of target sites (i.e. features)
  
  defaults
    - image collection = Sentinel 2 (i.e. 'COPERNICUS/S2')
    - targets = examples landcovers from International Geosphere 
      Biosphere Programme (IGBP): 
      https://code.earthengine.google.com/a2dc973ddff3556cdfc39c8d2506a188
  """
  
  def __init__(self):
    self.imageCollectionID = 'COPERNICUS/S2'
    self.startDate = '1900-01-01'
    self.stopDate = '2100-01-01'
    self.monthRange = (1,12)# i.e. default = whole year 
    self.sites = ee.FeatureCollection([
    ee.Feature(ee.Geometry.Point(-10.811, 35.353),{'landcover_type':'water'}),
    ee.Feature(ee.Geometry.Point(14.2575, 60.0484),{'landcover_type':'evergreen_needleleaf_forest'}),
    ee.Feature(ee.Geometry.Point(-71.917, -10.92),{'landcover_type':'evergreen_broadleaf_forest'}),
    ee.Feature(ee.Geometry.Point(127.3975, 60.9518),{'landcover_type':'deciduous_needleleaf_forest'}),
    ee.Feature(ee.Geometry.Point(-62.0673, -24.9462),{'landcover_type':'deciduous_broadleaf_forest'}),
    ee.Feature(ee.Geometry.Point(135.7031, 46.6306),{'landcover_type':'mixed_forest'}),
    ee.Feature(ee.Geometry.Point(40.4153, 4.3889),{'landcover_type':'closed_shrubland'}),
    ee.Feature(ee.Geometry.Point(129.672, -23.695),{'landcover_type':'open_shrubland'}),
    ee.Feature(ee.Geometry.Point(25.4855, -13.1437),{'landcover_type':'woody_savanna'}),
    ee.Feature(ee.Geometry.Point(27.235, 8.429),{'landcover_type':'savanna'}),
    ee.Feature(ee.Geometry.Point(-105.59, 44.056),{'landcover_type':'grassland'}),
    ee.Feature(ee.Geometry.Point(-85.4084, 53.3596),{'landcover_type':'permanent_wetland'}),
    ee.Feature(ee.Geometry.Point(75.4239, 30.5623),{'landcover_type':'cropland'}),
    ee.Feature(ee.Geometry.Point(-99.1393, 19.4407),{'landcover_type':'urban'}),
    ee.Feature(ee.Geometry.Point(102.4915, 14.7589),{'landcover_type':'cropland_and_natural_vegetation_mosaic'}),
    ee.Feature(ee.Geometry.Point(-43.86, 67.27),{'landcover_type':'snow_and_ice'}),
    ee.Feature(ee.Geometry.Point(21.094, 25.602),{'landcover_type':'barren_or_sparsely_vegetated'})
  ])
   
  def getProperties(self, img, geom):
    """
    gets properties for this img and geom (i.e. assetID, altitude, etc.)
    """
    
    imgID = img.get('system:index')
    assetID = ee.String(self.imageCollectionID+'/').cat(ee.String(imgID))

    global_dem = ee.Image('USGS/GMTED2010').rename(['altitude'])
    altitude =  global_dem.reduceRegion(ee.Reducer.mean(),geom)

    properties = ee.Dictionary({
      'assetID':assetID,
      'date':ee.Date(img.get('system:time_start')),
      #'cloud_cover':ee.Number(img.get('CLOUDY_PIXEL_PERCENTAGE')),#<-- Sentinel 2 specific
      'valid':1,
      'altitude':ee.Number(altitude.get('altitude'))
      })
    
    return properties
  
  def assetFinder(self, feature):
    """
    Finds assetIDs: will be mapped over feature collection of target sites
    """
    
    geom = feature.geometry()
    
    images = ee.ImageCollection(self.imageCollectionID)\
      .filterBounds(geom)\
      .filterDate(ee.Date(self.startDate),ee.Date(self.stopDate))\
      .filter(ee.Filter.calendarRange(self.monthRange[0],self.monthRange[1],'month'))

    # user define filters
    if self.useFilters:
      images = images.filter(self.useFilters)

    img = ee.Image(images.first())
    
    properties = ee.Algorithms.If(img,\
      self.getProperties(img, geom),\
      ee.Dictionary({'assetID':'None','valid':0})\
      )
    
    return ee.Feature(geom,properties).copyProperties(feature)
  
  def findAssets(self):
    fc = self.sites
    return fc.map(self.assetFinder)