from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

import pygame as pg

from ...builtin.components import Padding, GlobalElement, Scrollable, Camera
from ..state.rect import CoordinateValue
from ..elements import Element, Scene
from .display import DisplayManager
from .input import InputManager

if TYPE_CHECKING:
    from .workspace import Workspace


class ElementHierarchyManager:
    _forwarded = (
        'children',
        'descendants',
        'add_child',
        'is_ancestor_of',
        'is_parent_of',
        'get_element_rect'
    )

    children: list[Element]
    descendants: list[Element]

    def __init__(self, workspace: Workspace, display_manager: DisplayManager, input_manager: InputManager) -> None:
        self.workspace = workspace
        self.display = display_manager
        self.input_manager = input_manager

        self.children: list[Element] = []
        self._descendant_tree: dict[Element, list[Element]] = {}
        self.descendants: list[Element] = []

    def add_child(self, child: Element, z: int | None = None) -> None:
        if z is not None:
            child._z = z
        child.parent = self

    def is_ancestor_of(self, descendant: Element) -> bool:
        return descendant.is_descendant_of(self)

    def is_parent_of(self, child: Element) -> bool:
        return child._parent is self

    def _reprocess_descendants(self):
        self._descendants = []
        for child, child_desc in self._descendant_tree.items():
            self._descendants.append(child)
            self._descendants.extend(child_desc)

    def _resort_children(self):
        self.children.sort(key=lambda child: child.z)
        self.display._draw_surface_dirty = True

    def _propagate_visual_change(self, order: bool = False):
        self.display._draw_surface_dirty = True
        if order:
            self.workspace._element_input_manager.order_dirty = True

    def _propagate_layout_change(
        self,
        parent: bool = True,
        position: bool = False,
        updates_children: bool = False
    ):
        self.display._draw_surface_dirty = True

    def _get_global_children(self) -> Generator[Element, None, None]:
        for child in self.children:
            if child.get_component(GlobalElement):
                yield child

    def get_element_rect(self, element: Element) -> pg.Rect:
        parent = element.parent
        if isinstance(parent, Element):
            parent_rect = self.get_element_rect(parent)
            layout_rect = parent_rect.copy()

            if not element.ignores_environment:
                camera = parent.get_component(Camera)
                if camera is not None:
                    layout_rect.x -= int(camera.x)
                    layout_rect.y -= int(camera.y)

                scrollable = parent.get_component(Scrollable)
                if scrollable is not None:
                    layout_rect.x -= int(scrollable.x)
                    layout_rect.y -= int(scrollable.y)
        else:
            parent_rect = pg.Rect((0, 0), self.display.size)
            layout_rect = parent_rect.copy()

        padding = element.parent.get_component(Padding) if isinstance(element.parent, Element) and not element.ignores_environment else None

        rect_x = round(element.scale.x * layout_rect.w) + element.offset.x + layout_rect.x
        rect_y = round(element.scale.y * layout_rect.h) + element.offset.y + layout_rect.y
        rect_w = round(element.scale.w * layout_rect.w) + element.offset.w
        rect_h = round(element.scale.h * layout_rect.h) + element.offset.h

        rect = pg.Rect(rect_x, rect_y, rect_w, rect_h)

        if padding:
            pad_x = round(padding.scale * parent_rect.w) + padding.offset
            pad_y = round(padding.scale * parent_rect.h) + padding.offset
            inner_rect = parent_rect.inflate(-pad_x * 2, -pad_y * 2)

            dist = None
            if rect.x < parent_rect.x:
                dist = inner_rect.x - parent_rect.x
            elif rect.x < inner_rect.x:
                dist = inner_rect.x - rect.x
            if dist:
                rect.x += dist
                rect.w -= dist

            if rect.right > parent_rect.right:
                rect.w += inner_rect.right - parent_rect.right
            elif rect.right > inner_rect.right:
                rect.w = inner_rect.right - rect.x

            dist = None
            if rect.y < parent_rect.y:
                dist = inner_rect.y - parent_rect.y
            elif rect.y < inner_rect.y:
                dist = inner_rect.y - rect.y
            if dist:
                rect.y += dist
                rect.h -= dist

            if rect.bottom > parent_rect.bottom:
                rect.h += inner_rect.bottom - parent_rect.bottom
            elif rect.bottom > inner_rect.bottom:
                rect.h = inner_rect.bottom - rect.y

        rect.w = max(rect.w, 0)
        rect.h = max(rect.h, 0)
        return rect

    def _clips_descendants(self, element: Element) -> bool:
        return isinstance(element, Scene) or getattr(element, "scrollable", False)

    def _point_within_clip_ancestors(self, element: Element, point: CoordinateValue) -> bool:
        parent = element.parent
        while isinstance(parent, Element):
            if self._clips_descendants(parent) and not self.get_element_rect(parent).collidepoint(point):
                return False
            parent = parent.parent
        return True

    def _is_element_hittable(self, element: Element) -> bool:
        if not element.visible:
            return False
        rect = self.get_element_rect(element)
        if rect.w <= 0 or rect.h <= 0:
            return False
        if not rect.collidepoint(self.input_manager.state.mouse_pos):
            return False
        return self._point_within_clip_ancestors(element, self.input_manager.state.mouse_pos)


__all__ = [
    "ElementHierarchyManager",
]
