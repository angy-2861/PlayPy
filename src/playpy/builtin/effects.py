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
        self.color = color
        self.width = width
        self.edge_type: OutlineEdgeType = edge_type
        self.corner_type: OutlineCornerType = corner_type
        self._outline_dirty = True
        self._current_outline_surface: pg.Surface

    @property
    def outline_offset(self):
        factor = 1 if self.edge_type == "outset" else .5 if self.edge_type == "middle" else 0
        offset = int(factor * self.width)
        return state.Rect(-offset, -offset, 2 * offset, 2 * offset)
    
    def _propagate_layout_change(self, parent: bool = False, child: bool = False):
        self._outline_dirty = True
        super()._propagate_layout_change(parent, child)

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
        self.radius = radius

    def draw(self, workspace: elements.Workspace, current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler | None:
        rect = self.get_rect_px(workspace)

        surf = resources._make_surface(rect.size)

        pg.draw.rect(surf, (255, 255, 255, 255), surf.get_rect(), border_radius=self.radius)

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
        self.start_color = start_color
        self.end_color = end_color
        self.direction: GradientDirection = direction

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

def _normalize_button_gradient(
    grad: Gradient | tuple[state.ColorValue, state.ColorValue, GradientDirection] | tuple[state.ColorValue, state.ColorValue] | None,
) -> tuple[state.ColorValue, state.ColorValue, GradientDirection]:
    if grad is None:
        return ((0, 0, 0), (255, 255, 255), "vertical")
    if isinstance(grad, Gradient):
        return (grad.start_color, grad.end_color, grad.direction)
    if len(grad) == 2:
        return (*grad, "vertical")
    return grad

class ButtonGradient(Gradient):
    def __init__(
        self,
        idle_grad: Gradient | tuple[state.ColorValue, state.ColorValue, GradientDirection] | tuple[state.ColorValue, state.ColorValue] | None = None,
        hovered_grad: Gradient | tuple[state.ColorValue, state.ColorValue, GradientDirection] | tuple[state.ColorValue, state.ColorValue] | None = None,
        pressed_grad: Gradient | tuple[state.ColorValue, state.ColorValue, GradientDirection] | tuple[state.ColorValue, state.ColorValue] | None = None,
        scale: state.FRectValue = (0, 0, 1, 1),
        offset: state.RectValue = (0, 0, 0, 0),
        visible: bool = True,
        enabled: bool = True,
        z: int = -1_100_000,
        ignores_environment: bool = True,
    ):
        self.idle_grad = _normalize_button_gradient(idle_grad)
        self.hovered_grad = _normalize_button_gradient(hovered_grad)
        self.pressed_grad = _normalize_button_gradient(pressed_grad)
        self.current_grad = self.idle_grad

        super().__init__(self.current_grad[0], self.current_grad[1], self.current_grad[2], scale, offset, visible, enabled, z, ignores_environment)

    def _update_grad(self):
        self.start_color = self.current_grad[0]
        self.end_color = self.current_grad[1]
        self.direction = self.current_grad[2]

    def idle(self):
        self.current_grad = self.idle_grad
        self._update_grad()

    def hover(self):
        self.current_grad = self.hovered_grad
        self._update_grad()

    def press(self):
        self.current_grad = self.pressed_grad
        self._update_grad()

    def handle_input(self, workspace: elements.Workspace) -> None:
        if isinstance(self.parent, Button):
            if self.parent._pressed:
                self.press()
            elif self.parent.is_mouse_over(workspace):
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
        self.visual = visual
        self.blend_mode = blend_mode

    def handle_input(self, workspace: elements.Workspace) -> None:
        return None

    def draw(self, workspace: elements.Workspace, current_surface) -> state.SurfaceHandler:
        rect = self.get_rect_px(workspace)
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
