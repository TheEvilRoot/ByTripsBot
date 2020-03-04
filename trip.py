from enum import Enum


class VariantCompareResult(Enum):
    DIFFERENT = 1
    SEATS_SET_LESS = 2
    SEATS_SET_MORE = 3
    NO_MORE_SEATS = 4
    PRICE_DIFFERENT = 5
    EQUAL = 6


class Variant(object):
    def __init__(self, key, obj):
        self.key = key
        self.obj = obj

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self.obj[item]

    def to_message(self, lines):
        return lines + [f"{self.departure_time} {self.seats}/{self.all_seats} {self.price} BYN"]

    def short_name(self):
        return f"{self.departure_time} {self.price}"

    def compare(self, other):
        if other.departure_time == self.departure_time and other.datetime == self.datetime:
            if other.price != self.price:
                return VariantCompareResult.PRICE_DIFFERENT
            elif other.seats < self.seats:
                return VariantCompareResult.NO_MORE_SEATS if other.seats == 0 else VariantCompareResult.SEATS_SET_LESS
            elif other.seats > self.seats:
                return VariantCompareResult.SEATS_SET_MORE
            else:
                return VariantCompareResult.EQUAL
        else:
            return VariantCompareResult.DIFFERENT


class Trip(object):
    def __init__(self, route, data):
        self.trips = [Variant(key, value) for (key, value) in data.items() if value["route"] == route]

    def to_message(self, lines, only_with_seats=False):
        trips_lines = []
        for trip in self.trips:
            if trip.seats > 0:
                trips_lines = trip.to_message(trips_lines)
        return lines + trips_lines

    def __len__(self):
        return len(self.trips)

    def compare(self, other):
        results = []
        for new in other.trips:
            for old in self.trips:
                res = old.compare(new)
                if res != VariantCompareResult.DIFFERENT and res != VariantCompareResult.EQUAL:
                    results.append((res, old, new))
        return results
