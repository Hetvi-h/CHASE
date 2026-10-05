import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, Point
from pyproj import Transformer
import math

def generate_voronoi_polygons(zones_data, city_lat, city_lng, city_radius_km=15):
    if not zones_data or len(zones_data) < 2:
        return {}

    # Define a custom azimuthal equidistant projection centered on the city
    proj_str = f"+proj=aeqd +lat_0={city_lat} +lon_0={city_lng} +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    transformer_to_m = Transformer.from_crs("epsg:4326", proj_str, always_xy=True)
    transformer_to_latlng = Transformer.from_crs(proj_str, "epsg:4326", always_xy=True)

    points = []
    zone_ids = []
    for z in zones_data:
        x, y = transformer_to_m.transform(z['lng'], z['lat'])
        points.append([x, y])
        zone_ids.append(z['zone_id'])

    points = np.array(points)

    # To ensure bounded voronoi, we add dummy points far away
    radius_m = city_radius_km * 1000
    R = radius_m * 10
    dummy_points = [
        [R, 0], [-R, 0], [0, R], [0, -R],
        [R, R], [R, -R], [-R, R], [-R, -R]
    ]
    all_points = np.vstack([points, dummy_points])

    vor = Voronoi(all_points)

    city_boundary = Point(0, 0).buffer(radius_m)

    result = {}
    for i, p_idx in enumerate(vor.point_region[:len(points)]):
        region = vor.regions[p_idx]
        if not region or -1 in region:
            continue
        
        polygon_coords = [vor.vertices[i] for i in region]
        poly = Polygon(polygon_coords)
        
        # Clip to city boundary
        clipped_poly = poly.intersection(city_boundary)
        
        if clipped_poly.is_empty:
            continue
            
        if clipped_poly.geom_type == 'MultiPolygon':
            clipped_poly = max(clipped_poly.geoms, key=lambda a: a.area)
            
        # Convert back to lat/lng
        latlng_coords = []
        for x, y in clipped_poly.exterior.coords:
            lng, lat = transformer_to_latlng.transform(x, y)
            latlng_coords.append([lat, lng])
            
        result[zone_ids[i]] = latlng_coords

    return result
