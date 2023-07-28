from .geometry_utils import measure_distance


class TPoint:
    def __init__(self, t, pt) -> None:
        self.t = t
        self.pt = pt


def get_speed(tpt0, tpt1, is_latlon, conversion):
    d = measure_distance(tpt0.pt, tpt1.pt, is_latlon)
    d = d * conversion.crs / conversion.distance
    v = d / (tpt1.t - tpt0.t).total_seconds() * conversion.time
    return v


def get_speed2(pt0, pt1, delta_t, is_latlon, conversion):
    d = measure_distance(pt0, pt1, is_latlon)
    d = d * conversion.crs / conversion.distance
    v = d / delta_t.total_seconds() * conversion.time
    return v
