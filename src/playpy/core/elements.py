from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generator, TypeVar, TYPE_CHECKING, cast
from datetime import datetime

import pygame as pg
import colorama as clr

from .state import FRect, Rect, FRectValue, RectValue, SurfaceHandler, CoordinateValue
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
                self._parent._propagate_layout_change()

        self._parent = value

        # Attach to new parent, replacing existing component of same type.
        if value is not None:
            existing = value._components.get(type(self))
            if existing is not None and existing is not self:
                existing._parent = None
            value._components[type(self)] = self

            value._propagate_layout_change()

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
        self._ancestors: list[Element | Workspace] = []
        self._descendant_tree: dict[Element, list[Element]] = {}
        self._descendants: list[Element] = []
        self._root: ElementHierarchyManager | None = None

        self._scale: FRect = scale if isinstance(scale, FRect) else FRect(scale)
        self._offset: Rect = offset if isinstance(offset, Rect) else Rect(offset)

        self.enabled: bool = enabled
        self._visible: bool = visible
        self._z: int = z

        self._components: dict[type[Component], Component] = {}

        self.block_input_when_occluded: bool = block_input_when_occluded
        self.ignores_environment: bool = ignores_environment

        self._own_handler: SurfaceHandler | None = None
        self._own_handler_dirty: bool = True
        self._position_dirty: bool = True
        self._full_handler: SurfaceHandler | None = None
        self._full_handler_dirty: bool = True

    @property
    def scale(self):
        return self._scale
    
    @scale.setter
    def scale(self, value: FRect):
        if self._scale == value: return
        self._propagate_layout_change(
            updates_children=(
                value.width != self._scale.width or
                value.height != self._scale.height
            ),
            position=True
        )
        self._scale = value

    @property
    def offset(self):
        return self._offset
    
    @offset.setter
    def offset(self, value: Rect):
        if self._offset == value: return
        self._propagate_layout_change(
            updates_children=(
                value.width != self._offset.width or
                value.height != self._offset.height
            ),
            position=True
        )
        self._offset = value

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
        self._propagate_visual_change()

    @property
    def root(self) -> "Workspace | None":
        if self._root is not None: return self._root.workspace

    @property
    def parent(self) -> "Element | Workspace | None":
        return self._parent.workspace if not isinstance(self._parent, Element) and self._parent is not None else self._parent

    def _reprocess_descendants(self):
        self._descendants = []
        for child, child_desc in self._descendant_tree.items():
            self._descendants.append(child)
            self._descendants.extend(child_desc)

    def _update_ancestors_from_parent(self):
        if self._parent is None:
            self._ancestors = []
        elif isinstance(self._parent, Element):
            self._ancestors = [self._parent] + self._parent._ancestors
        else:
            self._ancestors = [self._parent.workspace]

    @parent.setter
    def parent(self, value: "Element | ElementHierarchyManager | Workspace | None"):
        value = cast("Element | ElementHierarchyManager | None", getattr(value, "_element_hierarchy_manager", value))
        if value is self._parent: return
        old = self._parent
        self._parent = value
        if resources._debug: print(f"{clr.Fore.GREEN}{clr.Style.BRIGHT}{datetime.now().strftime('[%d %b %Y - %H:%M:%S]')} - Moving {self} from parent {old} to parent {self.parent}{clr.Style.RESET_ALL}")
        # updates for old parent
        if old is not None:
            if resources._detailed_debug: print(f'{clr.Fore.YELLOW}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - Updating old parent descendants.{clr.Style.RESET_ALL}')
            # old children update
            old.children.remove(self)
            old._propagate_layout_change(updates_children=True, position=True)

            # old descendant update
            del old._descendant_tree[self]
            old._reprocess_descendants()
            if resources._detailed_debug: print(f'{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - Successfully updated descendants for old parent{clr.Style.RESET_ALL}')
            # ancestors need this descendant update too
            current_child = old
            while isinstance(current_child, Element) and current_child._parent is not None:
                current_child._parent._descendant_tree[current_child] = current_child._descendants
                current_child._parent._reprocess_descendants()
                if resources._detailed_debug: print(f'{clr.Fore.BLUE}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - Successfully updated descendants for old\'s ancestor {current_child.parent}, which is the parent of {current_child}. {clr.Style.RESET_ALL}')
                current_child = current_child._parent
                    
        if self._parent is not None:
            if resources._detailed_debug: print(f'{clr.Fore.YELLOW}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - Updating new parent descendants.{clr.Style.RESET_ALL}')
            # new children update
            self._parent.children.append(self)
            self._parent._propagate_layout_change(updates_children=True, position=True)
            self._parent._resort_children()

            # new descendant update
            self._parent._descendant_tree[self] = self._descendants
            self._parent._reprocess_descendants()
            if resources._detailed_debug: print(f'{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - Successfully descendants children for new parent{clr.Style.RESET_ALL}')
            # ancestors need this descendant update too
            current_child = self._parent
            while isinstance(current_child, Element) and current_child._parent is not None:
                current_child._parent._descendant_tree[current_child] = current_child._descendants
                current_child._parent._reprocess_descendants()
                if resources._detailed_debug: print(f'{clr.Fore.BLUE}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - Successfully updated descendants for new\'s ancestor {current_child.parent}, which is the parent of {current_child}. {clr.Style.RESET_ALL}')
                current_child = current_child._parent

        # ancestory tree updates
        self._update_ancestors_from_parent()
        # descendants need this update too
        for desc in self._descendants: desc._update_ancestors_from_parent()

    @property
    def ancestors(self) -> "list[Workspace | Element]":
        return self._ancestors

    @property
    def children(self) -> list["Element"]:
        return self._children

    @property
    def descendants(self) -> list["Element"]:
        return self._descendants
    
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

    def set_component(self, component: Component) -> None:
        component.parent = self

    def get_component(self, mod_type: type[_T_comp]) -> _T_comp | None:
        return cast(_T_comp | None, self._components.get(mod_type))

    def remove_component(self, mod_type: type) -> None:
        if mod_type in self._components:
            self._components[mod_type].parent = None

    def _resort_children(self):
        self.children.sort(key=lambda x: x.z)
        self._propagate_visual_change(True)

    def _propagate_visual_change(self, order: bool = False, ancestors_handled: bool = False):
        self._own_handler_dirty = True
        self._full_handler_dirty = True

        if ancestors_handled: return

        for ancestor in self._ancestors:
            if isinstance(ancestor, Element):
                ancestor._full_handler_dirty = True
            else:
                ancestor._display._draw_surface_dirty = True
                if order:
                    ancestor._element_input_manager.order_dirty = True

    def _propagate_layout_change(
        self,
        parent: bool = False,
        child: bool = False,
        position: bool = False,
        updates_children: bool = False,
    ):
        # propagate into children if doing so does anything
        if not parent and (position or updates_children):
            for ch in self.children: ch._propagate_layout_change(child=True, position=position, updates_children=updates_children)

            # extra functionality: only set position dirty when in base element or descendant
            if position:
                self._position_dirty = True

        # dirty handler if not a child or if this propagation updates children
        if not child or position or updates_children:
            self._full_handler_dirty = True

            # dirty myself if I am the base element or this propagation updates children and I am a child
            if not parent: self._propagate_visual_change(ancestors_handled=True)

        # only propagate up if not a child
        if child: return

        if self._parent is not None:
            self._parent._propagate_layout_change(parent=True, position=position, updates_children=updates_children)

            # also propagate to siblings
            for sib in self._parent.children:
                if sib is self: continue
                sib._propagate_layout_change(parent=True, child=True, position=position, updates_children=updates_children)

    def updated_pos(self, workspace: "Workspace", current_surface: SurfaceHandler | None) -> CoordinateValue | None:
        return workspace.get_element_rect(self).topleft

    @abstractmethod
    def draw(self, workspace: "Workspace", current_surface: SurfaceHandler | None) -> SurfaceHandler | None: ...

    @abstractmethod
    def handle_input(self, workspace: "Workspace") -> Generator[None, None, None] | None: ...

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

    def __repr__(self) -> str:
        return f"{type(self).__name__}(scale={self.scale},offset={self.offset},enabled={self.enabled},visible={self.visible}).parent = {type(self.parent).__name__}(...)"

    def __str__(self) -> str:
        return f"{type(self).__name__}@{self.scale}+{self.offset} ( {'⚙' if self.enabled else 'X'} , {'👁' if self.visible else 'X'} )"

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

        self._own_handler_dirty: bool = False

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
