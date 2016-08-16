from collections import namedtuple
import math


class Point(namedtuple('Point', ['time', 'latitude', 'longitude', 'altitude'])):
    __slots__ = ()

    def __str__(self):
        return "[" + (", ".join(str(p) for p in self)) + "]"


earth_radius = 3960.0


def latitude_to_miles(miles):
    """Given a distance north, return the change in latitude."""
    return math.degrees(miles / earth_radius)


def longitude_to_miles(miles, latitude):
    """Given a latitude and a distance west, return the change in longitude."""
    # Find the radius of a circle around the earth at given latitude.
    r = earth_radius * math.cos(math.radians(latitude))
    return math.degrees(miles / r)


def miles_to_latitude(change):
    """Given a latitude change, return the change in miles"""
    return math.radians(change) * earth_radius


def miles_to_longitude(change, latitude):
    """Given a latitude and change in longitude, return the change in miles"""
    r = earth_radius * math.cos(math.radians(latitude))
    return math.radians(change) * r
