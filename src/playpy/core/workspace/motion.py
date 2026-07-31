from __future__ import annotations
from typing import TYPE_CHECKING

from ..state import Tween, Animation
from ..resources import log, Severity, InvalidValue

if TYPE_CHECKING:
    from .workspace import Workspace


class MotionManager:
    _forwarded = {
        "active_tweens",
        "add_tween",
        "remove_tween",
        "get_tween",
        "clear_tweens",
        "active_animations",
        "add_animation",
        "remove_animation",
        "get_animation",
        "clear_animations",
    }

    active_tweens: list[Tween]
    active_animations: list[Animation]

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

        self.active_tweens = []
        self.active_animations = []

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

    def add_animation(self, animation: Animation, /) -> int:
        index = len(self.active_animations)
        self.active_animations.append(animation)
        return index

    def remove_animation(self, animation: Animation | int, /) -> Animation:
        if isinstance(animation, Animation):
            if animation not in self.active_animations:
                log(Severity.ERROR, InvalidValue, f"Provided animation {animation} cannot be removed because it is not active.", frames_back=1)
                return tween
            animation = self.active_animations.index(animation)
        popped = self.active_animations.pop(animation)
        popped.stop()
        return popped

    def get_animation(self, animation_index: int, /) -> Animation:
        if not (-len(self.active_animations) <= animation_index < len(self.active_animations)):
            log(Severity.ERROR, InvalidValue, f"Provided animation index {animation_index} is not present.", frames_back=1)
            return
        return self.active_animations[animation_index]
    
    def clear_animations(self) -> list[Animation]:
        cleared = self.active_animations.copy()
        for anim in cleared: anim.stop()
        self.active_animations.clear()
        return cleared

    def next_frame(self, dt: float) -> None:
        for tween in self.active_tweens.copy():
            removed = tween.update(dt)
            if removed: self.active_tweens.remove(tween)
        for anim in self.active_animations.copy(): anim.update(dt)

__all__ = [
    "MotionManager"
]
