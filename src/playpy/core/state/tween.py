from __future__ import annotations

from typing import Any, Literal, Protocol, TypeVar, overload, runtime_checkable
from collections.abc import Callable, Sequence, Mapping

from .. import resources


@runtime_checkable
class _SupportsAddAndMul(Protocol):
    def __add__(self, other) -> _SupportsAddAndMul: ...
    def __mul__(self, other) -> _SupportsAddAndMul: ...

TweenedValueHierarchyType = Literal["standalone", "attribute", "key", "index"]

class TweenedValue:
    def __init__(self, base_object: object | None, key: Any) -> None:
        self._base = base_object
        self._key = key
        self._hierarchy_type: TweenedValueHierarchyType | None = None
        if self._base is None:
            self._hierarchy_type = "standalone"
        else:
            if isinstance(self._base, Sequence) and isinstance(self._key, int) and len(self._base) > self._key >= -len(self._base):
                self._hierarchy_type = "index"
            elif isinstance(self._base, Mapping) and self._key in self._base:
                self._hierarchy_type = "key"
            else:
                try:
                    getattr(self._base, self._key)  # type: ignore
                    self._hierarchy_type = "attribute"
                except (AttributeError, TypeError):
                    resources.log(resources.Severity.ERROR, resources.InvalidValue, f"Could not find object {self._key} in base {self._base}", frames_back=1)

    @property
    def hierarchy_type(self):
        return self._hierarchy_type

    def get(self) -> Any:
        if self._hierarchy_type == "standalone":
            return self._key
        elif self._hierarchy_type == "attribute":
            try:
                return getattr(self._base, self._key)
            except AttributeError:
                resources.log(resources.Severity.ERROR, resources.InvalidValue, f"attribute {self._key} of instance {self._base} has been removed.", frames_back=1)
        elif self._hierarchy_type == "index" or self._hierarchy_type == "key":
            try:
                return self._base[self._key]  # type: ignore
            except (IndexError, KeyError):
                if self._hierarchy_type == "index":
                    resources.log(resources.Severity.ERROR, resources.InvalidValue, f"index {self._key} of sequence {self._base} has been removed.", frames_back=1)
                else:
                    resources.log(resources.Severity.ERROR, resources.InvalidValue, f"key {self._key} of mapping {self._base} has been removed.", frames_back=1)
        else:
            resources.log(resources.Severity.CRITICAL, resources.InvalidValue, f"hierarchy type of this TweenedValue is invalid: {self._hierarchy_type}", frames_back=1)

    def set(self, value: Any) -> None:
        if self._hierarchy_type == "standalone":
            self._key = value
        elif self._hierarchy_type == "attribute":
            try:
                setattr(self._base, self._key, value)
            except AttributeError:
                resources.log(resources.Severity.ERROR, resources.InvalidValue, f"attribute {self._key} of instance {self._base} has been removed.", frames_back=1)
        elif self._hierarchy_type == "index" or self._hierarchy_type == "key":
            try:
                self._base[self._key] = value  # type: ignore
            except (IndexError, KeyError):
                if self._hierarchy_type == "index":
                    resources.log(resources.Severity.ERROR, resources.InvalidValue, f"index {self._key} of sequence {self._base} has been removed.", frames_back=1)
                else:
                    resources.log(resources.Severity.ERROR, resources.InvalidValue, f"key {self._key} of mapping {self._base} has been removed.", frames_back=1)
        else:
            resources.log(resources.Severity.CRITICAL, resources.InvalidValue, f"hierarchy type of this TweenedValue is invalid: {self._hierarchy_type}", frames_back=1)


TweenEasingFunction = Literal["cubic", "quadratic", "exponential", "back", "bounce"]
TweenEasingStyle = Literal["in", "out", "in-out"]

def bounce(x: float):
    if x <= .25:
        return -16 * x**2 + 4 * x
    elif x < .75:
        return -8 * x**2 + 8 * x - 1.5
    else:
        return 4 * x - 3
    

easing_functions: dict[TweenEasingFunction, Callable[[float], float]] = {
    "cubic": lambda x: x**3,
    "quadratic": lambda x: x**2,
    "exponential": lambda x: 0 if x <= 0 else 2 ** (10 * (x - 1)),
    "back": lambda x: 2 * x**2 - x,
    "bounce": bounce,
}
easing_styles: dict[TweenEasingStyle, Callable[[Callable[[float], float]], Callable[[float], float]]] = {
    "in": lambda f: f,
    "out": lambda f: lambda x: 1 - f(1 - x),
    "in-out": lambda f: lambda x: (f(2*x)/2) if x <= .5 else (1-f(2*(1-x))/2),
}

class Tween:
    def __init__(
        self,
        tweened: list[TweenedValue],
        target: list[Any],
        easing_function: TweenEasingFunction | Callable[[float], float] = "cubic",
        easing_style: TweenEasingStyle | None = None,
        length: float = 1,
        looped: bool = False,
        clear_on_finish: bool = True
    ) -> None:
        self._tweened_values = tweened
        self._originals = [value.get() for value in self._tweened_values]
        self._targets = target
        self.edit_easing(easing_function, easing_style)
        self.length = length
        self.looped = looped
        self.clear_on_finish = clear_on_finish
        self._t = 0.
        self.playing = False
        self.stopped = False

    @property
    def tweened(self):
        return self._tweened_values

    @property
    def elapsed(self):
        return self._t * self.length
    
    @elapsed.setter
    def elapsed(self, value: float):
        self._t = value / self.length

    @property
    def finished(self):
        return not self.looped and self._t >= 1

    def edit_easing(self, easing_function: TweenEasingFunction | Callable[[float], float] = "cubic", easing_style: TweenEasingStyle | None = None):
        if callable(easing_function):
            if easing_function(0) != 0 or easing_function(1) != 1:
                resources.log(resources.Severity.ERROR, resources.InvalidValue, "Custom easing function must have anchors at (0, 0) and (1, 1)", frames_back=1)
        else:
            easing_function = easing_functions[easing_function]
        self._easing: Callable[[float], float] = (lambda x: x) if easing_style is None else easing_styles[easing_style](easing_function)

    def play(self):
        self.playing = True

    def pause(self):
        self.playing = False

    def start(self):
        self._originals = [value.get() for value in self._tweened_values]
        self.restart()

    def restart(self):
        self._t = 0
        self.playing = True
        self.stopped = False

    def stop(self):
        self.playing = False
        self.stopped = True

    @overload
    def _lerp(self, x: _SupportsAddAndMul, y: _SupportsAddAndMul, t: float): ...
    @overload
    def _lerp(self, x: Sequence[_SupportsAddAndMul], y: Sequence[_SupportsAddAndMul], t: float): ...

    def _lerp(self, x, y, t: float):
        if isinstance(x, str) or isinstance(y, str):
            resources.log(resources.Severity.ERROR, resources.InvalidValue, "Tweened values cannot be strings.", frames_back=1)
            return
        if isinstance(x, Sequence):
            assert isinstance(y, Sequence)
            result = list(x)
            for ind, (i, j) in enumerate(zip(x, y)):
                result[ind] = self._lerp(i, j, t)
            return result
        else:
            if not isinstance(x, _SupportsAddAndMul) or not isinstance(y, _SupportsAddAndMul):
                resources.log(resources.Severity.ERROR, resources.InvalidValue, "All tweened values must be addable and multiplyable, or sequences of addable multiplyable objects.", frames_back=1)
                return
            return x + (y + x * -1) * t

    def update(self, dt: float) -> bool:
        if not self.playing or self.stopped: return False
        should_remove = False
        self._t += dt / self.length
        if self.looped:
            self._t %= 1
        elif self._t >= 1:
            self._t = 1
            self.stop()
            should_remove = self.clear_on_finish
        for i, value in enumerate(self._tweened_values):
            orig = self._originals[i]
            trg = self._targets[i]
            if not isinstance(orig, (_SupportsAddAndMul, Sequence)) or not isinstance(trg, (_SupportsAddAndMul, Sequence)):
                resources.log(resources.Severity.ERROR, resources.InvalidValue, "All tweened values must be addable and multiplyable, or sequences of addable multiplyable objects.", frames_back=1)
                continue
            value.set(self._lerp(orig, trg, self._t))  # type: ignore
        return should_remove

__all__ = [
    "TweenedValueHierarchyType",
    "TweenEasingFunction",
    "TweenEasingStyle",
    "TweenedValue",
    "Tween",
]