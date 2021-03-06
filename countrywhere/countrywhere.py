#!/usr/bin/python

try:
    import json
except ImportError:
    import simplejson as json
import datetime
import math
import os
import pickle


class tzwhere(object):
    SHORTCUT_DEGREES_LATITUDE = 1
    SHORTCUT_DEGREES_LONGITUDE = 1
    # By default, use the data file in our package directory
    DEFAULT_FILENAME = os.path.join(os.path.dirname(__file__),
        'countries.json')

    def __init__(self, filename=DEFAULT_FILENAME, read_pickle=False,
            write_pickle=False):

        input_file = open(filename, 'r')

        if read_pickle:
            print 'Reading pickle input file: %s' % filename
            featureCollection = pickle.load(input_file)
        else:
            print 'Reading json input file: %s' % filename
            featureCollection = json.load(input_file)

        input_file.close()

        if write_pickle:
            print 'Writing pickle output file: %s' % PICKLE_FILENAME
            f = open(PICKLE_FILENAME, 'w')
            pickle.dump(featureCollection, f, pickle.HIGHEST_PROTOCOL)
            f.close()


        self.timezoneNamesToPolygons = {}
        for feature in featureCollection['features']:

            tzname = feature['properties']['name']
            if feature['geometry']['type'] == 'Polygon':
                raw_poly = feature['geometry']['coordinates'][0]
                if raw_poly and not (tzname in self.timezoneNamesToPolygons):
                    self.timezoneNamesToPolygons[tzname] = []

                #WPS84 coordinates are [long, lat], while many conventions are [lat, long]
                #Our data is in WPS84.  Convert to an explicit format which geolib likes.
                poly = []
                for coordinate_pair in raw_poly:
                    lat = coordinate_pair[1]
                    lng = coordinate_pair[0]
                    poly.append({'lat': lat, 'lng': lng})
                self.timezoneNamesToPolygons[tzname].append(tuple(poly))
            elif feature['geometry']['type'] == 'MultiPolygon':
                for outer_poly in feature['geometry']['coordinates']:
                    raw_poly = outer_poly[0]
                    if raw_poly and not (tzname in self.timezoneNamesToPolygons):
                        self.timezoneNamesToPolygons[tzname] = []
        
                    #WPS84 coordinates are [long, lat], while many conventions are [lat, long]
                    #Our data is in WPS84.  Convert to an explicit format which geolib likes.
                    poly = []
                    for coordinate_pair in raw_poly:
                        lat = coordinate_pair[1]
                        lng = coordinate_pair[0]
                        poly.append({'lat': lat, 'lng': lng})
                    self.timezoneNamesToPolygons[tzname].append(tuple(poly))

        self.timezoneLongitudeShortcuts = {};
        self.timezoneLatitudeShortcuts = {};
        for tzname in self.timezoneNamesToPolygons:
            for polyIndex, poly in enumerate(self.timezoneNamesToPolygons[tzname]):
                lats = [x['lat'] for x in poly]
                lngs = [x['lng'] for x in poly]
                minLng = math.floor(min(lngs) / self.SHORTCUT_DEGREES_LONGITUDE) * self.SHORTCUT_DEGREES_LONGITUDE;
                maxLng = math.floor(max(lngs) / self.SHORTCUT_DEGREES_LONGITUDE) * self.SHORTCUT_DEGREES_LONGITUDE;
                minLat = math.floor(min(lats) / self.SHORTCUT_DEGREES_LATITUDE) * self.SHORTCUT_DEGREES_LATITUDE;
                maxLat = math.floor(max(lats) / self.SHORTCUT_DEGREES_LATITUDE) * self.SHORTCUT_DEGREES_LATITUDE;
                degree = minLng
                while degree <= maxLng:
                    if degree not in self.timezoneLongitudeShortcuts:
                        self.timezoneLongitudeShortcuts[degree] = {}

                    if tzname not in self.timezoneLongitudeShortcuts[degree]:
                        self.timezoneLongitudeShortcuts[degree][tzname] = []

                    self.timezoneLongitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + self.SHORTCUT_DEGREES_LONGITUDE

                degree = minLat
                while degree <= maxLat:
                    if degree not in self.timezoneLatitudeShortcuts:
                        self.timezoneLatitudeShortcuts[degree] = {}

                    if tzname not in self.timezoneLatitudeShortcuts[degree]:
                        self.timezoneLatitudeShortcuts[degree][tzname] = []

                    self.timezoneLatitudeShortcuts[degree][tzname].append(polyIndex)
                    degree = degree + self.SHORTCUT_DEGREES_LATITUDE

        #convert things to tuples to save memory
        for tzname in self.timezoneNamesToPolygons.keys():
            self.timezoneNamesToPolygons[tzname] = tuple(self.timezoneNamesToPolygons[tzname])
        for degree in self.timezoneLatitudeShortcuts:
            for tzname in self.timezoneLatitudeShortcuts[degree].keys():
                self.timezoneLatitudeShortcuts[degree][tzname] = tuple(self.timezoneLatitudeShortcuts[degree][tzname])
        for degree in self.timezoneLongitudeShortcuts.keys():
            for tzname in self.timezoneLongitudeShortcuts[degree].keys():
                self.timezoneLongitudeShortcuts[degree][tzname] = tuple(self.timezoneLongitudeShortcuts[degree][tzname])

    def _point_inside_polygon(self, x, y, poly, buffer=0):
        n = len(poly)
        inside =False

        p1x, p1y = poly[0]['lng'], poly[0]['lat']
        for i in range(n+1):
            p2x,p2y = poly[i % n]['lng'], poly[i % n]['lat']
            if y+buffer > min(p1y,p2y):
                if y-buffer <= max(p1y,p2y):
                    if x-buffer <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y

        return inside

    def tzNameAt(self, latitude, longitude):
        latTzOptions = self.timezoneLatitudeShortcuts.get(math.floor(latitude / self.SHORTCUT_DEGREES_LATITUDE) * self.SHORTCUT_DEGREES_LATITUDE, {})
        latSet = set(latTzOptions.keys());
        lngTzOptions = self.timezoneLongitudeShortcuts.get(math.floor(longitude / self.SHORTCUT_DEGREES_LONGITUDE) * self.SHORTCUT_DEGREES_LONGITUDE, {})
        lngSet = set(lngTzOptions.keys())
        possibleTimezones = lngSet.intersection(latSet);
        
        if possibleTimezones:
            if len(possibleTimezones) == 1:
                return possibleTimezones.pop()
            else:
                for buffer_multiplier in xrange(20):
                    buffer = .05*buffer_multiplier
                    for tzname in possibleTimezones:
                        polyIndices = set(latTzOptions[tzname]).intersection(set(lngTzOptions[tzname]));
                        for polyIndex in polyIndices:
                            poly = self.timezoneNamesToPolygons[tzname][polyIndex]
                            if self._point_inside_polygon(longitude, latitude, poly, buffer=buffer):
                                return tzname

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='''
    Convert lat/lng to timezones. Specify --read_pickle to initialize from a pickle file instead of the json file.
''')
    parser.add_argument('--json_file', default='countries.json',
                    help='path to the json input file')
    parser.add_argument('--pickle_file', default='tz_world.pickle',
                    help='path to the pickle input file')
    parser.add_argument('--read_pickle', action='store_true',
                    help='read pickle data instead of json')
    parser.add_argument('--write_pickle', action='store_true',
                    help='whether to output a pickle file')
    args = parser.parse_args()

    if args.read_pickle:
        filename = args.pickle_file
    else:
        filename = args.json_file

    start = datetime.datetime.now()
    w = tzwhere(filename, args.read_pickle, args.write_pickle)
    end = datetime.datetime.now()
    print 'Initialized in: ',
    print end-start
    #print w.tzNameAt(float(35.295953), float(-89.662186)) #Arlington, TN
    #print w.tzNameAt(float(33.58), float(-85.85)) #Memphis, TN
    #print w.tzNameAt(float(61.17), float(-150.02)) #Anchorage, AK
    #print w.tzNameAt(float(44.12), float(-123.22)) #Eugene, OR
    #print w.tzNameAt(float(42.652647), float(-73.756371)) #Albany, NY
    print w.tzNameAt(49.2166667,-2.1325)
    print w.tzNameAt(40.679, -73.984)
    print w.tzNameAt(32.743, -117.249)
