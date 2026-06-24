from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator, TypeVar, TYPE_CHECKING, cast

import pygame as pg

from .state import FRect, Rect, FRectValue, RectValue, SurfaceHandler
from . import resources

if TYPE_CHECKING:
    from .workspace import Workspace
    from .workspace.element_hierarchy import ElementHierarchyManager

_T_comp = TypeVar("_T_comp", bound="Component")

class Component:
    def __init__(self) -> None:
        resources.require_init()
        self._parent: "Element | None" = None

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value: "Element | None"):
        if value is self._parent:
            return

        # Detach from existing parent, if still registered there.
        if self._parent is not None:
            current = self._parent._components.get(type(self))
            if current is self:
                del self._parent._components[type(self)]

        self._parent = value

        # Attach to new parent, replacing existing component of same type.
        if value is not None:
            existing = value._components.get(type(self))
            if existing is not None and existing is not self:
                existing._parent = None
            value._components[type(self)] = self

    @parent.deleter
    def parent(self):
        self.parent = None

class Element(ABC):
    def __init__(
        self,
        scale: FRectValue,
        offset: RectValue,
        visible: bool = True,
        enabled: bool = True,
        block_input_when_occluded: bool = False,
        z: int = 0,
        ignores_environment: bool = False,
    ):
        resources.require_init()
        self._children: list[Element] = []
        self._parent: Element | ElementHierarchyManager | None = None
        self.scale: FRect = scale if isinstance(scale, FRect) else FRect(scale)
        self.offset: Rect = offset if isinstance(offset, Rect) else Rect(offset)
        self.enabled: bool = enabled
        self._visible: bool = visible
        self._z: int = z
        self._components: dict[type[Component], Component] = {}
        self.block_input_when_occluded: bool = block_input_when_occluded
        self.ignores_environment: bool = ignores_environment

    @property
    def visible(self) -> bool:
        if not isinstance(self._parent, Element):
            return self._visible
        return self._visible and self._parent.visible
    
    @visible.setter
    def visible(self, value: bool):
        self._visible = value
        if value and isinstance(self._parent, Element) and not self._parent.visible:
            self._parent.visible = value

    @property
    def parent(self) -> "Element | Workspace | None":
        return self._parent.workspace if not isinstance(self._parent, Element) and self._parent is not None else self._parent

    @parent.setter
    def parent(self, value: "Element | ElementHierarchyManager | Workspace | None"):
        if self._parent is not None:
            self._parent.children.remove(self)
        self._parent = cast("Element | ElementHierarchyManager | None", getattr(value, "_element_hierarchy_manager", value))
        if self._parent is not None:
            self._parent.children.append(self)
            self._parent._resort_children()

    @property
    def ancestors(self) -> "list[Workspace | Element]":
        if self.parent is None:
            return []
        elif isinstance(self.parent, Element):
            return self.parent.ancestors + [self.parent]
        else:
            return [self.parent]

    @property
    def children(self) -> list["Element"]:
        return self._children
    
    @property
    def descendants(self) -> list["Element"]:
        descendants: list[Element] = []
        for child in self._children:
            descendants.append(child)
            descendants.extend(child.descendants)
        return descendants
    
    @property
    def z(self) -> int:
        return self._z
    
    @z.setter
    def z(self, value: int):
        self._z = value
        if self._parent is not None:
            self._parent._resort_children()

    def add_child(self, child: "Element", z: int | None = None) -> None:
        if z is not None:
            child._z = z
        child.parent = self

    def remove_child(self, child: "Element") -> None:
        child.parent = None

    def set_component(self, component: Component) -> None:
        component.parent = self

    def get_component(self, mod_type: type[_T_comp]) -> _T_comp | None:
        return self._components.get(mod_type)  # type: ignore

    def remove_component(self, mod_type: type) -> None:
        if mod_type in self._components:
            self._components[mod_type].parent = None

    def _resort_children(self):
        self.children.sort(key=lambda x: x.z)
        self._propagate_order_change()

    def _propagate_order_change(self):
        if self._parent is not None:
            self._parent._propagate_order_change()

    def _propagate_layout_change(
        self,
        parent: bool = False,
        child: bool = False,
    ):
        if not parent:
            for ch in self.children: ch._propagate_layout_change(child=True)
        if child: return
        if self._parent is not None:
            self._parent._propagate_layout_change(parent=True)
            for sib in self._parent.children:
                if sib is self: continue
                sib._propagate_layout_change(parent=True, child=True)

    @abstractmethod
    def draw(self, workspace: "Workspace", current_surface: SurfaceHandler | None) -> SurfaceHandler | None: ...

    @abstractmethod
    def handle_input(self, workspace: "Workspace") -> Generator[None, None, None] | None: ...

    def get_rect_px(self, workspace: "Workspace") -> pg.Rect:
        return workspace._element_hierarchy_manager.get_element_rect(self)

    def is_mouse_over(self, workspace: "Workspace") -> bool:
        return workspace._element_input_manager.is_mouse_over(self)

    def is_mouse_top(self, workspace: "Workspace") -> bool:
        return workspace._element_input_manager.is_mouse_top(self)
    
    def is_descendant_of(self, ancestor: "Element | ElementHierarchyManager | Workspace") -> bool:
        current = self._parent
        while current is not None:
            if current is ancestor or not isinstance(current, Element) and current.workspace is ancestor:
                return True
            if not isinstance(current, Element):
                break
            current = current._parent
        return False

    def is_ancestor_of(self, descendant: "Element") -> bool:
        return descendant.is_descendant_of(self)

    def is_parent_of(self, child: "Element") -> bool:
        return child._parent is self
    
    def is_child_of(self, parent: "Element"):
        return parent.is_parent_of(self)
    
    def destroy(self):
        self.parent = None
        for child in self.children:
            child.destroy()

class Scene(Element):
    def __init__(
        self,
        scale: FRectValue | None = None,
        offset: RectValue | None = None,
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        name: str | None = None,
    ):
        if scale is None:
            scale = (0, 0, 1, 1)
        if offset is None:
            offset = (0, 0, 0, 0)
        super().__init__(scale, offset, visible=visible, enabled=enabled, z=z)
        self.name = name

    def on_enter(self, workspace: "Workspace"):
        pass

    def on_exit(self, workspace: "Workspace"):
        pass

    def on_pause(self, workspace: "Workspace"):
        pass

    def on_resume(self, workspace: "Workspace"):
        pass

    def draw(self, workspace: "Workspace", current_handler: SurfaceHandler | None):
        pass

    def handle_input(self, workspace: "Workspace"):
        pass

__all__ = [
    "Component",
    "Element",
    "Scene",
]
