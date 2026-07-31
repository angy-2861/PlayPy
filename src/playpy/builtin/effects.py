import math
from typing import Literal

import numpy as np
import pygame as pg
from scipy.ndimage import binary_dilation

from ..core import state
from ..core import elements
from ..core import resources
from .elements import Button


__all__ = [
    "Effect",
    "OutlineEdgeType",
    "OutlineCornerType",
    "Outline",
    "BorderRadius",
    "GradientDirection",
    "Gradient",
    "GradientValue",
    "ButtonGradient",
    "VisualLayer"
]
    
class Effect(elements.Element):
    def __init__(
        self,
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = True,
    ):
        super().__init__(scale, offset, visible, enabled, False, z, ignores_environment)

    def handle_input(self, workspace: elements.Workspace) -> None:
        return
    
def color_change_isnoalpha(val1: state.ColorValue, val2: state.ColorValue):
    return (
        len(val1) == len(val2) or
        len(val1) == 4 and val1[3] == 255 or
        len(val2) == 4 and val2[3] == 255
    )

OutlineEdgeType = Literal["inset", "middle", "outset"]
OutlineCornerType = Literal["square", "rounded", "pointed"]

class Outline(Effect):
    def __init__(
        self,
        color: state.ColorValue = (0, 0, 0),
        width: int = 5,
        edge_type: OutlineEdgeType = "middle",
        corner_type: OutlineCornerType = "square",
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        visible: bool = True,
        enabled: bool = True,
        z: int = 1_000_002,
        ignores_environment: bool = True,
    ):
        super().__init__(scale, offset, visible, enabled, z, ignores_environment)
        self._color = color
        self._width = width
        self._edge_type: OutlineEdgeType = edge_type
        self._corner_type: OutlineCornerType = corner_type
        self._outline_dirty = True
        self._current_outline_surface: pg.Surface

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, value: state.ColorValue):
        if color_change_isnoalpha(self._color, value): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._color = value

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value: int | float):
        self._propagate_layout_change()
        self._width = int(value)
    
    @property
    def edge_type(self):
        return self._edge_type
    
    @edge_type.setter
    def edge_type(self, value: OutlineEdgeType):
        self._propagate_layout_change()
        self._edge_type = value
    
    @property
    def corner_type(self):
        return self._corner_type
    
    @corner_type.setter
    def corner_type(self, value: OutlineCornerType):
        self._propagate_layout_change()
        self._corner_type = value

    @property
    def outline_offset(self):
        factor = 1 if self.edge_type == "outset" else .5 if self.edge_type == "middle" else 0
        offset = int(factor * self.width)
        return state.Rect(-offset, -offset, 2 * offset, 2 * offset)

    def _create_grid_for_brush(self, radius: int):
        size = 2 * radius + 1

        x = np.arange(size) - radius
        y = np.arange(size) - radius

        grid = np.meshgrid(x, y)
        
        return grid
    
    def _create_brush(self, radius: int):
        if self.corner_type == "square":
            size = 2 * radius + 1
            return np.ones((size, size)).astype(bool)
        
        X, Y = self._create_grid_for_brush(radius)

        if self.corner_type == "pointed":
            return abs(X) + abs(Y) <= abs(radius)
        else:
            return (X ** 2 + Y ** 2) <= (radius ** 2)

    def _create_outline(self, current_surface: state.SurfaceHandler, pad: int = 0) -> np.ndarray:
        occupied = pg.surfarray.pixels_alpha(current_surface.surface) > 0
        occupied = np.pad(occupied, pad)

        empty = ~occupied

        neighbor_mask = np.array([
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ], dtype=bool)

        touches_empty = binary_dilation(empty, neighbor_mask).astype(bool)
        outline_source = occupied & touches_empty

        radius = self.width // 2 if self.edge_type == "middle" else self.width
        brush = self._create_brush(radius)

        outline = binary_dilation(outline_source, brush).astype(bool)

        if self.edge_type == "middle":
            return outline
        elif self.edge_type == "inset":
            return outline & occupied
        else:
            return outline & empty
        
    def _outline_to_surface(self, outline: np.ndarray) -> pg.Surface:
        surf = resources._make_surface(outline.shape)

        color = self.color
        if len(color) == 3:
            color = (*color, 255)

        alpha = pg.surfarray.pixels_alpha(surf)
        alpha[:, :] = outline.astype(np.uint8) * color[3]
        del alpha

        rgb = pg.surfarray.pixels3d(surf)
        rgb[:, :, 0] = color[0]
        rgb[:, :, 1] = color[1]
        rgb[:, :, 2] = color[2]
        del rgb

        return surf
    
    def updated_pos(self, workspace, current_surface: state.SurfaceHandler | None) -> state.CoordinateValue | None:
        if current_surface is None: return
        pad = self.width if self.edge_type != "inset" else 0
        return (
            current_surface.pos[0] - pad,
            current_surface.pos[1] - pad,
        )

    def draw(self, workspace, current_surface: state.SurfaceHandler | None):
        if current_surface is None: return
        
        pad = self.width if self.edge_type != "inset" else 0

        outline = self._create_outline(current_surface, pad)
        surf = self._outline_to_surface(outline)

        pos = (
            current_surface.pos[0] - pad,
            current_surface.pos[1] - pad,
        )

        return state.SurfaceHandler(
            surf,
            pos
        )

class BorderRadius(Effect):
    def __init__(
        self,
        radius: int = 0,
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        visible: bool = True,
        enabled: bool = True,
        z: int = 1_000_000,
        ignores_environment: bool = True,
    ):
        super().__init__(scale, offset, visible, enabled, z, ignores_environment)
        self._radius = radius

    @property
    def radius(self):
        return self._radius
    
    @radius.setter
    def radius(self, value: int):
        self._radius = value
        self._propagate_layout_change()

    def draw(self, workspace: elements.Workspace, current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler | None:
        rect = workspace.get_element_rect(self)

        surf = resources._make_surface(rect.size)

        pg.draw.rect(surf, (255, 255, 255), surf.get_rect(), border_radius=self.radius)

        return state.SurfaceHandler(surf, rect.topleft, state.BlendMode.RGB_ALPHA_MULTIPLY)

GradientDirection = Literal["vertical", "horizontal", "radial"]

def _lerp_color(a: state.ColorValue, b: state.ColorValue, t: float) -> tuple[int, int, int, int]:
    if len(a) == 3:
        a = (a[0], a[1], a[2], 255)
    if len(b) == 3:
        b = (b[0], b[1], b[2], 255)
    return (
        round(a[0] + (b[0] - a[0]) * t),
        round(a[1] + (b[1] - a[1]) * t),
        round(a[2] + (b[2] - a[2]) * t),
        round(a[3] + (b[3] - a[3]) * t),
    )

class Gradient(Effect):
    def __init__(
        self,
        start_color: state.ColorValue = (0, 0, 0),
        end_color: state.ColorValue = (255, 255, 255),
        direction: GradientDirection = "vertical",
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        visible: bool = True,
        enabled: bool = True,
        z: int = -1_100_000,
        ignores_environment: bool = True,
    ):
        super().__init__(scale, offset, visible, enabled, z, ignores_environment)
        self._start_color = start_color
        self._end_color = end_color
        self._direction: GradientDirection = direction

    @property
    def start_color(self):
        return self._start_color
    
    @start_color.setter
    def start_color(self, value: state.ColorValue):
        if color_change_isnoalpha(self._start_color, value): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._start_color = value

    @property
    def end_color(self):
        return self._end_color
    
    @end_color.setter
    def end_color(self, value: state.ColorValue):
        if color_change_isnoalpha(self._end_color, value): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._end_color = value
    
    @property
    def direction(self):
        return self._direction
    
    @direction.setter
    def direction(self, value: GradientDirection):
        self._propagate_visual_change()
        self._direction = value

    def make_gradient_surface(self, size: tuple[int, int]) -> pg.Surface:
        grad_surf = resources._make_surface(size)

        width, height = size

        if self.direction == "radial":
            end = math.ceil(max(size) / 2)
            center = (width // 2, height // 2)
        elif self.direction == "horizontal":
            end = width
        else:
            end = height

        pos = 0
        while pos < end:
            t = pos / end
            color = _lerp_color(self.start_color, self.end_color, t)
            if self.direction == "radial":
                pg.draw.circle(grad_surf, color, center, pos, width=1)
                continue
            elif self.direction == "horizontal":
                point1, point2 = (pos, 0), (pos, height)
            else:
                point1, point2 = (0, pos), (width, pos)
            pg.draw.line(grad_surf, color, point1, point2)
            pos += 1

        return grad_surf

    def updated_pos(self, workspace, current_surface: state.SurfaceHandler | None) -> state.CoordinateValue | None:
        if current_surface is None: return
        return current_surface.pos

    def draw(self, workspace, current_surface: state.SurfaceHandler | None):
        if current_surface is None: return

        surf = self.make_gradient_surface(current_surface.surface.get_size())

        original_alpha = pg.surfarray.pixels_alpha(current_surface.surface).copy()
        surf_alpha = pg.surfarray.pixels_alpha(surf)

        surf_alpha[:, :] = (
            original_alpha.astype(np.uint16)
            * surf_alpha.astype(np.uint16)
            // 255
        ).astype(np.uint8)
        del surf_alpha

        return state.SurfaceHandler(
            surf,
            current_surface.pos,
        )

GradientValue = Gradient | tuple[state.ColorValue, state.ColorValue, GradientDirection] | tuple[state.ColorValue, state.ColorValue] | None

def _normalize_button_gradient(
    grad: GradientValue,
) -> tuple[state.ColorValue, state.ColorValue, GradientDirection]:
    if grad is None:
        return ((0, 0, 0), (255, 255, 255), "vertical")
    if isinstance(grad, Gradient):
        return (grad.start_color, grad.end_color, grad.direction)
    if len(grad) == 2:
        return (*grad, "vertical")
    return grad

def grad_change_isnoalpha(val1: tuple[state.ColorValue, state.ColorValue, GradientDirection], val2: tuple[state.ColorValue, state.ColorValue, GradientDirection]):
    return (
        color_change_isnoalpha(val1[0], val2[0]) and
        color_change_isnoalpha(val1[1], val2[1])
    )

class ButtonGradient(Gradient):
    def __init__(
        self,
        idle_grad: GradientValue = None,
        hovered_grad: GradientValue = None,
        pressed_grad: GradientValue = None,
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        visible: bool = True,
        enabled: bool = True,
        z: int = -1_100_000,
        ignores_environment: bool = True,
    ):
        self._idle_grad = _normalize_button_gradient(idle_grad)
        self._hovered_grad = _normalize_button_gradient(hovered_grad)
        self._pressed_grad = _normalize_button_gradient(pressed_grad)
        self._current_grad = self._idle_grad

        super().__init__(self.current_grad[0], self.current_grad[1], self.current_grad[2], scale, offset, visible, enabled, z, ignores_environment)

    @property
    def idle_grad(self):
        return self._idle_grad

    @idle_grad.setter
    def idle_grad(self, value: GradientValue):
        normalized = _normalize_button_gradient(value)
        if grad_change_isnoalpha(self._idle_grad, normalized): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._idle_grad = normalized

    @property
    def hovered_grad(self):
        return self._hovered_grad

    @hovered_grad.setter
    def hovered_grad(self, value: GradientValue):
        normalized = _normalize_button_gradient(value)
        if grad_change_isnoalpha(self._hovered_grad, normalized): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._hovered_grad = normalized

    @property
    def pressed_grad(self):
        return self._pressed_grad

    @pressed_grad.setter
    def pressed_grad(self, value: GradientValue):
        normalized = _normalize_button_gradient(value)
        if grad_change_isnoalpha(self._pressed_grad, normalized): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._pressed_grad = normalized

    @property
    def current_grad(self):
        return self._current_grad

    @current_grad.setter
    def current_grad(self, value: GradientValue):
        normalized = _normalize_button_gradient(value)
        if grad_change_isnoalpha(self._current_grad, normalized): self._propagate_visual_change()
        else: self._propagate_layout_change()
        self._current_grad = normalized

    def _update_grad(self):
        self._start_color = self._current_grad[0]
        self._end_color = self._current_grad[1]
        self._direction = self._current_grad[2]

    def idle(self):
        if self.current_grad == self.idle_grad: return
        self.current_grad = self.idle_grad
        self._update_grad()

    def hover(self):
        if self.current_grad == self.hovered_grad: return
        self.current_grad = self.hovered_grad
        self._update_grad()

    def press(self):
        if self.current_grad == self.pressed_grad: return
        self.current_grad = self.pressed_grad
        self._update_grad()

    def handle_input(self, workspace: elements.Workspace) -> None:
        if isinstance(self.parent, Button):
            if self.parent._pressed:
                self.press()
            elif workspace.is_mouse_over(self.parent):
                self.hover()
            else:
                self.idle()
    
class VisualLayer(Effect):
    def __init__(
        self,
        visual: state.Sprite | state.Animation | state.ColorValue,
        blend_mode: state.BlendMode | None = None,
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        z: int = -1_000_000,
        visible: bool = True,
        enabled: bool = True,
        ignores_environment: bool = True,
    ):
        super().__init__(scale, offset, visible, enabled, z, ignores_environment)
        self._visual = visual
        self._blend_mode = blend_mode

    @property
    def visual(self):
        return self._visual
    
    @visual.setter
    def visual(self, value: state.Sprite | state.Animation | state.ColorValue):
        self._visual = value
        self._propagate_layout_change()

    @property
    def blend_mode(self):
        return self._blend_mode
    
    @blend_mode.setter
    def blend_mode(self, value: state.BlendMode | None):
        self._blend_mode = value
        self._propagate_layout_change()

    def handle_input(self, workspace: elements.Workspace) -> None:
        return None

    def draw(self, workspace: elements.Workspace, current_surface) -> state.SurfaceHandler:
        rect = workspace.get_element_rect(self)
        if isinstance(self.visual, tuple):
            color = self.visual
            if len(color) == 3:
                color = (*color, 255)
            surf = resources._make_surface(rect.size)
            surf.fill(color)
        else:
            sprite_obj = self.visual
            if isinstance(sprite_obj, state.Animation):
                sprite_obj = sprite_obj.current_frame
            surf = sprite_obj.load()
            if surf.get_size() != rect.size:
                surf = pg.transform.scale(surf, rect.size)
        return state.SurfaceHandler(surf, rect.topleft, 0 if self.blend_mode is None else self.blend_mode)
