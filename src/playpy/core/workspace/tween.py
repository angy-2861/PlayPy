from __future__ import annotations
from typing import TYPE_CHECKING

from ..state.tween import Tween
from ..resources import log, Severity, InvalidValue

if TYPE_CHECKING:
    from .workspace import Workspace


class TweenManager:
    _forwarded = {
        "active_tweens",
        "add_tween",
        "remove_tween",
        "get_tween",
        "clear_tweens",
    }

    active_tweens: list[Tween]

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

        self.active_tweens = []

    def add_tween(self, tween: Tween, /) -> int:
        index = len(self.active_tweens)
        self.active_tweens.append(tween)
        return index

    def remove_tween(self, tween: Tween | int, /) -> Tween:
        if isinstance(tween, Tween):
            if tween not in self.active_tweens:
                log(Severity.ERROR, InvalidValue, f"Provided tween {tween} cannot be removed because it is not active.", frames_back=1)
                return tween
            tween = self.active_tweens.index(tween)
        popped = self.active_tweens.pop(tween)
        popped.stop()
        return popped

    def get_tween(self, tween_index: int, /) -> Tween:
        if not (-len(self.active_tweens) <= tween_index < len(self.active_tweens)):
            log(Severity.ERROR, InvalidValue, f"Provided tween index {tween_index} is not present.", frames_back=1)
            return
        return self.active_tweens[tween_index]
    
    def clear_tweens(self) -> list[Tween]:
        cleared = self.active_tweens.copy()
        for tween in cleared: tween.stop()
        self.active_tweens.clear()
        return cleared

    def next_frame(self, dt: float) -> None:
        for tween in self.active_tweens.copy():
            removed = tween.update(dt)
            if removed: self.active_tweens.remove(tween)

__all__ = [
    "TweenManager"
]
