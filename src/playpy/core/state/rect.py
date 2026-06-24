from __future__ import annotations

from typing import Iterator, Literal, TypeIs, overload, Union

import pygame as pg

from .. import resources


CoordinateValue = tuple[int, int]
FCoordinateValue = tuple[float, float]
RectValue = Union[tuple[int, int, int, int], tuple[CoordinateValue, CoordinateValue], pg.Rect, "Rect"]
FRectValue = Union[tuple[float, float, float, float], tuple[FCoordinateValue, FCoordinateValue], "FRect"]

def _is_rect_xywh(arg) -> TypeIs[tuple[int, int, int, int]]:
    return isinstance(arg, tuple) and len(arg) == 4 and all(isinstance(scalar, int) for scalar in arg)

def _is_rect_topleft_size(arg) -> TypeIs[tuple[CoordinateValue, CoordinateValue]]:
    return isinstance(arg, tuple) and len(arg) == 2 and all(isinstance(point, tuple) and len(point) == 2 and all(isinstance(scalar, int) for scalar in point) for point in arg)

def _is_rect_rect_obj(arg) -> "TypeIs[pg.Rect | Rect]":
    return isinstance(arg, pg.Rect) or isinstance(arg, Rect)


def _is_frect_xywh(arg) -> TypeIs[tuple[float, float, float, float]]:
    return isinstance(arg, tuple) and len(arg) == 4 and all(isinstance(scalar, (int, float)) for scalar in arg)

def _is_frect_topleft_size(arg) -> TypeIs[tuple[FCoordinateValue, FCoordinateValue]]:
    return isinstance(arg, tuple) and len(arg) == 2 and all(isinstance(point, tuple) and len(point) == 2 and all(isinstance(scalar, float) for scalar in point) for point in arg)

def _is_frect_frect_obj(arg) -> "TypeIs[FRect]":
    return isinstance(arg, FRect)


@overload
def _validate_rect_args(args: tuple, frect: Literal[False] = False) -> tuple[int, int, int, int]: ...

@overload
def _validate_rect_args(args: tuple, frect: Literal[True]) -> tuple[float, float, float, float]: ...

def _validate_rect_args(args: tuple, frect: bool = False) -> tuple[int, int, int, int] | tuple[float, float, float, float]:
    if len(args) == 1:
        args = args[0]
    if _is_frect_xywh(args) or _is_rect_xywh(args):
        return args
    if _is_frect_topleft_size(args) or _is_rect_topleft_size(args):
        return args[0][0], args[0][1], args[1][0], args[1][1]
    elif _is_frect_frect_obj(args) or _is_rect_rect_obj(args):
        return (args.x, args.y, args.w, args.h) if isinstance(args, pg.Rect) else args.tuple()
    else:
        resources.log(resources.Severity.ERROR, resources.InvalidValue, f"Invalid arguments to {'F' if frect else ''}Rect constructor: {args}", frames_back=2)
    

class FRect:
    @overload
    def __init__(self, x: float, y: float, w: float, h: float, /) -> None: ...

    @overload
    def __init__(self, topleft: FCoordinateValue, size: FCoordinateValue, /) -> None: ...

    @overload
    def __init__(self, rect: FRectValue, /) -> None: ...

    def __init__(self, *args):
        if not (1 <= len(args) <= 4):
            resources.log(resources.Severity.ERROR, resources.InvalidValue, "FRect constructor takes 1 to 4 arguments")
        x, y, w, h = _validate_rect_args(args, True)
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    def __repr__(self) -> str:
        return f"FRect({self.tuple()})"

    def tuple(self) -> tuple[float, float, float, float]:
        return (self._x, self._y, self._w, self._h)
    
    def __iter__(self) -> Iterator[float]:
        return iter(self.tuple())
    
    def __add__(self, other: FRect):
        if not isinstance(other, FRect):
            return NotImplemented
        return FRect(self.x + other.x, self.y + other.y, self.w + other.w, self.h + other.h)

    def __mul__(self, other: FRect | float | int):
        if isinstance(other, FRect):
            return FRect(self.x * other.x, self.y * other.y, self.w * other.w, self.h * other.h)
        elif isinstance(other, (float, int)):
            return FRect(self.x * other, self.y * other, self.w * other, self.h * other)
        else:
            return NotImplemented

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new: float):
        self._x = new

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, new: float):
        self._y = new

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, new: float):
        self._w = new

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, new: float):
        self._h = new

    left = x
    top = y
    width = w
    height = h

    @property
    def right(self) -> float:
        return self._x + self._w
    
    @right.setter
    def right(self, new: float):
        self._x = new - self._w

    @property
    def bottom(self) -> float:
        return self._y + self._h
    
    @bottom.setter
    def bottom(self, new: float):
        self._y = new - self._h

    @property
    def topleft(self):
        return (self.x, self.y)
    
    @topleft.setter
    def topleft(self, new: FCoordinateValue):
        self.x, self.y = new

    @property
    def bottomleft(self):
        return (self.x, self.bottom)

    @bottomleft.setter
    def bottomleft(self, new: FCoordinateValue):
        self.x, self.bottom = new

    @property
    def topright(self):
        return (self.right, self.y)
    
    @topright.setter
    def topright(self, new: FCoordinateValue):
        self.right, self.y = new

    @property
    def bottomright(self):
        return (self.right, self.bottom)
    
    @bottomright.setter
    def bottomright(self, new: FCoordinateValue):
        self.right, self.bottom = new

    @property
    def center(self):
        return (self.x + self.w / 2, self.y + self.h / 2)
    
    @center.setter
    def center(self, new: FCoordinateValue):
        cx, cy = new
        self.x = cx - self.w / 2
        self.y = cy - self.h / 2

    def inflate(self, amount: float):
        result = self.copy()
        result.x -= amount / 2
        result.y -= amount / 2
        result.w += amount
        result.h += amount
        return result

    def collides_with(self, other: FRect | FCoordinateValue):
        if isinstance(other, FRect):
            return (
                self.right >= other.left and other.right >= self.left and # x checks
                self.bottom >= other.top and other.bottom >= self.top # y checks
            )
        else:
            return (
                self.left <= other[0] <= self.right and # x checks
                self.top <= other[1] <= self.bottom # y checks
            )

    def copy(self):
        return FRect(self.x, self.y, self.w, self.h)


class Rect:
    @overload
    def __init__(self, x: int, y: int, w: int, h: int, /) -> None: ...

    @overload
    def __init__(self, topleft: CoordinateValue, size: CoordinateValue, /) -> None: ...

    @overload
    def __init__(self, rect: RectValue, /) -> None: ...

    def __init__(self, *args):
        if not (1 <= len(args) <= 4):
            resources.log(resources.Severity.ERROR, resources.InvalidValue, "Rect constructor takes 1 to 4 arguments")
        x, y, w, h = _validate_rect_args(args)
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._rect = pg.Rect(x, y, w, h)

    def __repr__(self) -> str:
        return f"Rect{self.tuple()}"

    def tuple(self) -> tuple[int, int, int, int]:
        return (self._x, self._y, self._w, self._h)

    def __iter__(self) -> Iterator[int]:
        return iter(self.tuple())

    def __add__(self, other: Rect):
        if not isinstance(other, Rect):
            return NotImplemented
        return Rect(self.x + other.x, self.y + other.y, self.w + other.w, self.h + other.h)

    def __mul__(self, other: Rect | int):
        if isinstance(other, Rect):
            return Rect(self.x * other.x, self.y * other.y, self.w * other.w, self.h * other.h)
        elif isinstance(other, int):
            return Rect(self.x * other, self.y * other, self.w * other, self.h * other)
        else:
            return NotImplemented

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, new: int):
        self._x = new
        self._rect.x = new

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, new: int):
        self._y = new
        self._rect.y = new

    @property
    def w(self):
        return self._w

    @w.setter
    def w(self, new: int):
        self._w = new
        self._rect.w = new

    @property
    def h(self):
        return self._h

    @h.setter
    def h(self, new: int):
        self._h = new
        self._rect.h = new

    left = x
    top = y
    width = w
    height = h

    @property
    def right(self) -> int:
        return self._x + self._w
    
    @right.setter
    def right(self, new: int):
        self._x = new - self._w
        self._rect.right = new

    @property
    def bottom(self) -> int:
        return self._y + self._h
    
    @bottom.setter
    def bottom(self, new: int):
        self._y = new - self._h
        self._rect.bottom = new

    @property
    def topleft(self):
        return (self.x, self.y)
    
    @topleft.setter
    def topleft(self, new: CoordinateValue):
        self.x, self.y = new

    @property
    def bottomleft(self):
        return (self.x, self.bottom)

    @bottomleft.setter
    def bottomleft(self, new: CoordinateValue):
        self.x, self.bottom = new

    @property
    def topright(self):
        return (self.right, self.y)
    
    @topright.setter
    def topright(self, new: CoordinateValue):
        self.right, self.y = new

    @property
    def bottomright(self):
        return (self.right, self.bottom)
    
    @bottomright.setter
    def bottomright(self, new: CoordinateValue):
        self.right, self.bottom = new

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)
    
    @center.setter
    def center(self, new: CoordinateValue):
        cx, cy = new
        self.x = cx - self.w // 2
        self.y = cy - self.h // 2

    def inflate(self, amount: int):
        result = self.copy()
        result.x -= amount // 2
        result.y -= amount // 2
        result.w += amount
        result.h += amount
        return result

    def collides_with(self, other: Rect | CoordinateValue):
        if isinstance(other, Rect):
            return (
                self.right >= other.left and other.right >= self.left and # x checks
                self.bottom >= other.top and other.bottom >= self.top # y checks
            )
        else:
            return (
                self.left <= other[0] <= self.right and # x checks
                self.top <= other[1] <= self.bottom # y checks
            )

    def copy(self):
        return Rect(self.x, self.y, self.w, self.h)

def empty_rect():
    return Rect(0, 0, 0, 0)

def empty_frect():
    return FRect(0, 0, 0, 0)

def full_screen_rect():
    return (FRect(0, 0, 1, 1), empty_rect())

__all__ = [
    "RectValue",
    "FRectValue",
    "CoordinateValue",
    "FCoordinateValue",
    "FRect",
    "Rect",
    "empty_rect",
    "empty_frect",
    "full_screen_rect",
]
