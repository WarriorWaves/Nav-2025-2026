import math

class Iceberg:
    def __init__(self, lat, lon, heading_deg):
        self.lat = lat
        self.lon = lon
        self.heading = math.radians(heading_deg)

    def direction(self):
        return math.sin(self.heading), math.cos(self.heading)


class Platform:
    def __init__(self, name, lat, lon):
        self.name = name
        self.lat = lat
        self.lon = lon


class ThreatAnalyzer:
    def __init__(self, iceberg, platforms):
        self.iceberg = iceberg
        self.platforms = platforms

    def to_nm(self, lat1, lon1, lat2, lon2):
        dlat = (lat2 - lat1) * 60
        avg_lat = math.radians((lat1 + lat2) / 2)
        dlon = (lon2 - lon1) * 60 * math.cos(avg_lat)
        return dlat, dlon

    def closest_distance(self, platform):
        dlat, dlon = self.to_nm(self.iceberg.lat, self.iceberg.lon,
                                platform.lat, platform.lon)
        dx, dy = self.iceberg.direction()
        proj = dlat * dy + dlon * dx
        perp_lat = dlat - proj * dy
        perp_lon = dlon - proj * dx
        return math.sqrt(perp_lat**2 + perp_lon**2)

    def threat(self, dist):
        if dist > 10:
            return "Green"
        elif dist >= 5:
            return "Yellow"
        return "Red"

    def analyze(self):
        for p in self.platforms:
            dist = round(self.closest_distance(p), 2)
            print(f"{p.name}: {dist} nm → {self.threat(dist)}")


# fill ts out!!

if __name__ == "__main__":
    iceberg = Iceberg(46.0, -48.3, 45)

    platforms = [
        Platform("Hibernia", 43.7504, -48.7819),
        Platform("Sea Rose", 46.7895, -48.1417),
        Platform("Terra Nova", 46.4, -48.4),
        Platform("Hebron", 46.544, -48.498)
    ]

    ThreatAnalyzer(iceberg, platforms).analyze()
