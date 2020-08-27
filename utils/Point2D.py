import math
from numbers import Number

class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __abs__(self):
        return math.hypot(self.x, self.y)

    def __neg__(self):
        return Point2D(-self.x, -self.y)

    def __add__(self, other):
        return Point2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return self + (-other)

    def __mul__(self, other):
        assert isinstance(other, Number)
        return Point2D(self.x * other, self.y * other)

    def __rmul__(self, other):
        assert isinstance(other, Number)
        return Point2D(self.x * other, self.y * other)

    def __repr__(self):
        return f"<Point2D: ({self.x}, {self.y})>"

