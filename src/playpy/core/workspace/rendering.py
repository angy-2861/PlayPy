from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime

import colorama as clr

from .. import resources
from ..elements import Element
from ...builtin.effects import Effect
from ..state import SurfaceHandler, BlendMode
from .display import DisplayManager
from .scenes import SceneManager
from .element_hierarchy import ElementHierarchyManager

if TYPE_CHECKING:
    from .workspace import Workspace


DEBUG_DEPTH = 0

class Renderer:
    _forwarded = {}


    def __init__(self, workspace: Workspace, display_manager: DisplayManager, scene_manager: SceneManager, element_hierarchy_manager: ElementHierarchyManager) -> None:
        self.workspace = workspace
        self._display_manager = display_manager
        self._scene_manager = scene_manager
        self._element_hierarchy_manager = element_hierarchy_manager

    
    def draw_element(self, element: Element, parent_handler: SurfaceHandler | None):
        global _debug, _detailed_debug, DEBUG_DEPTH
        if resources._debug: print(f"{clr.Fore.YELLOW}{clr.Style.BRIGHT}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} drawing {element}{clr.Style.RESET_ALL}")

        # visibility check
        if not element.visible: return
        if resources._detailed_debug: print(f"{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} element {element} is visible{clr.Style.RESET_ALL}")

        # full dirtyness check
        if element._full_handler_dirty:
            if resources._detailed_debug: print(f"{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} element {element}'s full handler is dirty{clr.Style.RESET_ALL}")
            element._full_handler_dirty = False

            if element._full_handler is None:
                # create a blank canvas if the element has no full handler
                rect = self._element_hierarchy_manager.get_element_rect(element)
                element._full_handler = SurfaceHandler(resources._make_surface(rect.size),rect.topleft)
                if resources._detailed_debug: print(f"{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} created a blank full handler for element {element}, which did not have one{clr.Style.RESET_ALL}")
            else:
                # else just make the canvas blank (reuse the current surface instead of throwing it out for a new one)
                element._full_handler.surface.fill((0, 0, 0, 0))

            # own dirty check
            if element._own_handler_dirty:
                if resources._detailed_debug: print(f"{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} element {element}'s own handler is dirty{clr.Style.RESET_ALL}")
                element._own_handler = element.draw(self.workspace, parent_handler)
                element._own_handler_dirty = False

            # position dirty check
            if element._position_dirty and element._own_handler is not None:
                if resources._detailed_debug: print(f"{clr.Fore.MAGENTA}{clr.Style.DIM}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} element {element}'s position is dirty{clr.Style.RESET_ALL}")
                if (pos := element.updated_pos(self.workspace, parent_handler)) is not None:
                    element._own_handler.pos = pos
                    element._position_dirty = False
                    if resources._detailed_debug: print(f"{clr.Fore.CYAN}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} fixed position for element {element}{clr.Style.RESET_ALL}")

            # extend the full handler with the own handler if it is present
            if element._own_handler is not None:
                element._full_handler.special_flags = element._own_handler.special_flags
                element._full_handler.extend(element._own_handler)
                if resources._detailed_debug: print(f"{clr.Fore.CYAN}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} extended full handler with own handler for element {element}{clr.Style.RESET_ALL}")

            # recurse into children
            DEBUG_DEPTH += 1
            for child in element.children:
                child_handler = self.draw_element(child, element._full_handler)

                # if child has a handler, add it to our own
                if child_handler is not None:
                    if resources._debug: print(f"{clr.Fore.GREEN}{clr.Style.BRIGHT}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} we were able to draw child {child} onto element {element}'s surface{clr.Style.RESET_ALL}")
                    element._full_handler.extend(
                        child_handler,
                        clip_within_self=not child.ignores_environment,
                    )
            DEBUG_DEPTH -= 1

            if resources._debug: print(f"{clr.Fore.GREEN}{clr.Style.BRIGHT}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - {'>' * DEBUG_DEPTH} successfully updated full handler for element {element} (blend mode: {BlendMode.from_pygame(element._full_handler.special_flags)}){clr.Style.RESET_ALL}")

        return element._full_handler
    
    def draw(self):
        if not self._display_manager._draw_surface_dirty: return
        self._display_manager._draw_surface_dirty = False
        if resources._debug: print(f"{clr.Fore.RED}{clr.Style.BRIGHT}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - draw surface is dirty!{clr.Style.RESET_ALL}")
        self._display_manager.fill()

        scene = self._scene_manager.current_scene
        draw_order = None
        if scene is not None:
            draw_order = list(self._element_hierarchy_manager._get_global_children()) + [scene]

        for child in draw_order or self.workspace.children:
            child_handler = self.draw_element(child, self._display_manager.draw_surface)
            if child_handler is not None:
                if resources._debug: print(f"{clr.Fore.CYAN}{clr.Style.BRIGHT}{datetime.now().strftime("[%d %b %Y - %H:%M:%S]")} - we were able to draw element {child}{clr.Style.RESET_ALL}")
                self._display_manager.draw_surface.extend(child_handler, clip_within_self=True)


__all__ = [
    "Renderer"
]
