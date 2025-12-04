# routeapi/views.py
import csv
import os
import math
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from geopy.geocoders import Nominatim
from .utils import route_length_and_points_from_polyline, sample_along_route, haversine_miles
from .models import FuelStation
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response



# loads CSV directly if DB empty (fallback)
def load_fuel_list_from_csv():
    path = settings.FUEL_CSV_PATH
    stations = []
    if not os.path.exists(path):
        return stations
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for r in reader:
            stations.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'lat': float(r['lat']),
                'lon': float(r['lon']),
                'price': float(r['price'])
            })
    return stations

def get_all_stations():
    qs = list(FuelStation.objects.all().values('id','name','lat','lon','price'))
    if qs:
        return [{'id': str(x['id']), 'name': x['name'], 'lat': x['lat'], 'lon': x['lon'], 'price': x['price']} for x in qs]
    return load_fuel_list_from_csv()

def find_nearby_stations(point, stations, radius_miles):
    out = []
    for s in stations:
        d = haversine_miles(point, (s['lat'], s['lon']))
        if d <= radius_miles:
            out.append((s, d))
    out.sort(key=lambda x: x[1])
    return [x[0] for x in out]

class RouteFuelAPIView(APIView):
    def post(self, request):
        data = request.data
        start = data.get('start')
        finish = data.get('finish')
        if not start or not finish:
            return Response({'error': 'start and finish required'}, status=status.HTTP_400_BAD_REQUEST)

        # parse lat,lon or geocode
        def parse_loc(v):
            if isinstance(v, str) and ',' in v:
                try:
                    lat, lon = map(float, v.split(','))
                    return (lat, lon)
                except:
                    pass
            # geocode with Nominatim
            geolocator = Nominatim(user_agent='route-fuel-api')
            loc = geolocator.geocode(v, country_codes='us', timeout=10)
            if not loc:
                return None
            return (loc.latitude, loc.longitude)

        start_pt = parse_loc(start)
        finish_pt = parse_loc(finish)
        if not start_pt or not finish_pt:
            return Response({'error': 'could not geocode start or finish'}, status=status.HTTP_400_BAD_REQUEST)

        # call OSRM once
        coords = f"{start_pt[1]},{start_pt[0]};{finish_pt[1]},{finish_pt[0]}"
        osrm_url = f"{settings.OSRM_ROUTE_URL}/{coords}?overview=full&geometries=polyline"
        try:
            r = requests.get(osrm_url, timeout=15)
            r.raise_for_status()
        except Exception as exc:
            return Response({'error': 'routing failed', 'details': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        jr = r.json()
        if 'routes' not in jr or not jr['routes']:
            return Response({'error': 'no route returned'}, status=status.HTTP_502_BAD_GATEWAY)
        route = jr['routes'][0]
        distance_meters = route['distance']  # meters
        distance_miles = distance_meters / 1609.344
        polyline_str = route.get('geometry')

        # decode polyline and compute cumulative distances
        pts, cum = route_length_and_points_from_polyline(polyline_str)

        # compute number of fuel checkpoints
        vehicle_range = settings.VEHICLE_RANGE_MILES
        # how many refuels needed? we need ceil(distance / range) - maybe zero if within range
        num_refuels = 0
        if distance_miles > vehicle_range:
            # if distance is 790 and range is 500 -> 1 refuel (stop)
            num_refuels = math.ceil(distance_miles / vehicle_range) - 1

        # gather checkpoint positions: places along route where we should refuel
        checkpoints = []
        for i in range(1, num_refuels + 1):
            miles_along = min(distance_miles, i * vehicle_range)
            pos = sample_along_route(pts, cum, miles_along)
            checkpoints.append(pos)

        # load stations
        stations = get_all_stations()
        chosen_stops = []
        for cp in checkpoints:
            nearby = find_nearby_stations(cp, stations, settings.FUEL_SEARCH_RADIUS_MILES)
            if nearby:
                # pick cheapest among nearby
                station = min(nearby, key=lambda s: s['price'])
            else:
                # fallback to overall cheapest station
                if stations:
                    station = min(stations, key=lambda s: s['price'])
                else:
                    station = None
            if station:
                chosen_stops.append(station)

        # deduplicate
        dedup = []
        seen_coords = set()
        for s in chosen_stops:
            key = (round(s['lat'],5), round(s['lon'],5))
            if key not in seen_coords:
                dedup.append(s)
                seen_coords.add(key)
        chosen_stops = dedup

        # estimate fuel usage & cost
        total_gallons = distance_miles / settings.VEHICLE_MPG
        estimated_cost = None
        if chosen_stops:
            # allocate gallons proportional to trip segments (simple equal-split across stops + starting fuel)
            # simplest: total gallons buy across the stops equally
            gallons_per_stop = total_gallons / len(chosen_stops)
            total_cost = 0.0
            for s in chosen_stops:
                total_cost += gallons_per_stop * s['price']
            estimated_cost = round(total_cost, 2)
        else:
            # no stops found; estimate cost using global cheapest if exists
            if stations:
                cheapest = min(stations, key=lambda s: s['price'])
                estimated_cost = round(total_gallons * cheapest['price'], 2)

        # create a static map URL (using OSM static map demo) — simple fallback
        # markers: start green, finish red, stops blue
        map_base = 'https://staticmap.openstreetmap.de/staticmap.php'
        markers = []
        markers.append(f"{start_pt[0]},{start_pt[1]},lightgreen1")
        markers.append(f"{finish_pt[0]},{finish_pt[1]},red1")
        for s in chosen_stops:
            markers.append(f"{s['lat']},{s['lon']},blue1")
        marker_params = '&'.join([f"markers={m}" for m in markers])
        # add simplified path by sampling 20 points along route
        path_markers = []
        for i in range(21):
            pos = sample_along_route(pts, cum, cum[-1] * (i/20.0))
            path_markers.append(f"markers={pos[0]},{pos[1]},gray1")
        map_url = f"{map_base}?size=800x400&{marker_params}&{'&'.join(path_markers)}"

        return Response({
            'distance_miles': round(distance_miles, 2),
            'estimated_total_gallons': round(total_gallons, 2),
            'estimated_total_cost_usd': estimated_cost,
            'fuel_stops': chosen_stops,
            'map_image_url': map_url,
            'route_polyline': polyline_str,
        })

# If RouteResult model is in routeapi.models
try:
    from .models import RouteResult
except Exception:
    RouteResult = None  # defensive fallback

class RouteResultDetailAPIView(APIView):
    """
    GET /api/results/<uuid>/  -> returns stored RouteResult
    """
    def get(self, request, pk):
        if RouteResult is None:
            return Response({'error': 'RouteResult model not available on server.'}, status=500)

        obj = get_object_or_404(RouteResult, pk=pk)
        data = {
            'id': str(obj.id),
            'created_at': obj.created_at.isoformat() if obj.created_at else None,
            'start': obj.start,
            'finish': obj.finish,
            'distance_miles': obj.distance_miles,
            'estimated_total_gallons': obj.estimated_total_gallons,
            'estimated_total_cost_usd': obj.estimated_total_cost_usd,
            'fuel_stops': obj.fuel_stops,
            'map_image_url': obj.map_image_url,
            'route_polyline': obj.route_polyline,
            'raw_response': obj.raw_response,
        }
        return Response(data)
