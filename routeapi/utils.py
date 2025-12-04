# routeapi/utils.py
import math
from polyline import decode as polyline_decode

def haversine_miles(a, b):
    """Return great-circle distance in miles between two (lat,lon)."""
    lat1, lon1 = a
    lat2, lon2 = b
    # convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    aa = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(aa))
    return 3958.8 * c

def route_length_and_points_from_polyline(polyline_str):
    """Decode polyline and return list of points and cumulative distances (miles)."""
    pts = polyline_decode(polyline_str)  # returns list of (lat, lon)
    # compute cumulative distances
    cum = [0.0]
    for i in range(1, len(pts)):
        d = haversine_miles(pts[i-1], pts[i])
        cum.append(cum[-1] + d)
    return pts, cum

def sample_along_route(pts, cum_distances, desired_miles):
    """
    Return lat,lon at position desired_miles along route measured from start.
    Uses linear interpolation between the two points where desired_miles falls.
    """
    if desired_miles <= 0:
        return pts[0]
    if desired_miles >= cum_distances[-1]:
        return pts[-1]
    # find segment
    for i in range(1, len(cum_distances)):
        if cum_distances[i] >= desired_miles:
            prev = i-1
            # fraction along segment
            seg_dist = cum_distances[i] - cum_distances[prev]
            if seg_dist == 0:
                return pts[i]
            frac = (desired_miles - cum_distances[prev]) / seg_dist
            lat = pts[prev][0] + (pts[i][0] - pts[prev][0]) * frac
            lon = pts[prev][1] + (pts[i][1] - pts[prev][1]) * frac
            return (lat, lon)
    return pts[-1]
