from collections.abc import Callable, Generator

from ..core import state
from ..core import elements
from ..core import workspace
from .components import GlobalElement


__all__ = [
    "Event",
    "create_event",
    "on_start",
    "on_update",
    "on_quit",
    "on_resize",
    "on_maximize",
    "on_restore",
    "on_scene_change",
    "on_hover",
    "on_unhover",
    "while_hovered",
    "on_hover_inclusive",
    "on_unhover_inclusive",
    "while_hovered_inclusive",
    "on_profile_changed",
    "on_profile_added",
    "on_profile_removed",
    "on_controller_not_connected",
    "on_input_action_down",
    "on_input_action_up",
    "while_input_action",
    "on_key_down",
    "on_key_up",
    "while_key_held",
    "on_mousebutton_down",
    "on_mousebutton_up",
    "while_mousebutton_held",
    "on_controllerbutton_down",
    "on_controllerbutton_up",
    "while_controllerbutton_held",
]

class Event(elements.Element):
    def __init__(
        self,
        condition_function: Callable[[workspace.Workspace], bool],
        event_function: Callable[[workspace.Workspace], Generator[None, None, None] | None],
        negative_function: Callable[[workspace.Workspace], Generator[None, None, None] | None] | None = None,
        enabled: bool = True,
        once: bool = False,
        global_event: bool = True,
    ):
        super().__init__(state.empty_frect(), state.empty_rect(), False, enabled, False, 1_100_000)
        self.event_func = event_function
        self.cond_func = condition_function
        self.neg_func = negative_function
        self.once = once

        if global_event:
            GlobalElement().parent = self

    def draw(self, workspace: workspace.Workspace, current_handler: state.SurfaceHandler | None):
        pass

    def handle_input(self, workspace: workspace.Workspace):
        if self.cond_func(workspace):
            if self.once:
                self.enabled = False
            return self.event_func(workspace)
        elif self.neg_func:
            if self.once:
                self.enabled = False
            return self.neg_func(workspace)

def create_event(target: workspace.Workspace | elements.Scene, cond_func: Callable[[workspace.Workspace], bool]):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        new_event = Event(cond_func, event_func)
        new_event.parent = target
        return event_func
    return wrapper


def on_start(target: workspace.Workspace | elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        if isinstance(target, elements.Scene):
            new_event = Event(lambda w, scene=target: w.current_scene is scene and w.last_scene_change_time == w.input_state.runtime, event_func)
            new_event.parent = target
            return event_func
        new_event = Event(lambda w: w.input_state.runtime == 0, event_func, once=True)
        new_event.parent = target
        return event_func
    return wrapper

def on_update(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        if isinstance(target, elements.Scene):
            new_event = Event(lambda w, scene=target: w.current_scene is scene, event_func)
            new_event.parent = target
            return event_func
        new_event = Event(lambda w: True, event_func)
        new_event.parent = target
        return event_func
    return wrapper

def on_quit(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        new_event = Event(lambda w: w.input_state.quit, event_func)
        new_event.parent = target
        return event_func
    return wrapper


def on_resize(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        new_event = Event(lambda w: w.resized, event_func)
        new_event.parent = target
        return event_func
    return wrapper

def on_maximize(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        new_event = Event(lambda w: w.maxed, event_func)
        new_event.parent = target
        return event_func
    return wrapper

def on_restore(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        new_event = Event(lambda w: w.restored, event_func)
        new_event.parent = target
        return event_func
    return wrapper


def on_scene_change(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        if isinstance(target, elements.Scene):
            new_event = Event(
                lambda w, scene=target: w.scene_changed and w.current_scene is scene,
                event_func,
            )
            new_event.parent = target
            return event_func
        new_event = Event(lambda w: w.scene_changed, event_func)
        new_event.parent = target
        return event_func
    return wrapper


def on_hover(target: workspace.Workspace | elements.Scene, hovered: elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.just_hovered(hovered), event_func).parent = target
        return event_func
    return wrapper

def on_unhover(target: workspace.Workspace | elements.Scene, hovered: elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.just_unhovered(hovered), event_func).parent = target
        return event_func
    return wrapper

def while_hovered(target: workspace.Workspace | elements.Scene, hovered: elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.is_mouse_top(hovered), event_func).parent = target
        return event_func
    return wrapper

def on_hover_inclusive(target: workspace.Workspace | elements.Scene, hovered: elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.just_hovered_inclusive(hovered), event_func).parent = target
        return event_func
    return wrapper

def on_unhover_inclusive(target: workspace.Workspace | elements.Scene, hovered: elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.just_unhovered_inclusive(hovered), event_func).parent = target
        return event_func
    return wrapper

def while_hovered_inclusive(target: workspace.Workspace | elements.Scene, hovered: elements.Element):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.is_mouse_over(hovered), event_func).parent = target
        return event_func
    return wrapper


def on_profile_changed(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: bool(w.profile_changes), event_func).parent = target
        return event_func
    return wrapper

def on_profile_added(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: bool(w.profiles_added), event_func).parent = target
        return event_func
    return wrapper

def on_profile_removed(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: bool(w.profiles_removed), event_func).parent = target
        return event_func
    return wrapper

def on_controller_not_connected(target: workspace.Workspace | elements.Scene):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: bool(w.bad_joystick_indices), event_func).parent = target
        return event_func
    return wrapper


def on_input_action_down(target: workspace.Workspace | elements.Scene, action: state.InputAction):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.input_action_down(action), event_func).parent = target
        return event_func
    return wrapper

def on_input_action_up(target: workspace.Workspace | elements.Scene, action: state.InputAction):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.input_action_up(action), event_func).parent = target
        return event_func
    return wrapper

def while_input_action(target: workspace.Workspace | elements.Scene, action: state.InputAction):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.input_action_held(action), event_func).parent = target
        return event_func
    return wrapper


def on_key_down(target: workspace.Workspace | elements.Scene, key: state.KeyValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.key_down(key, profile), event_func).parent = target
        return event_func
    return wrapper

def on_key_up(target: workspace.Workspace | elements.Scene, key: state.KeyValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.key_up(key, profile), event_func).parent = target
        return event_func
    return wrapper

def while_key_held(target: workspace.Workspace | elements.Scene, key: state.KeyValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.key_held(key, profile), event_func).parent = target
        return event_func
    return wrapper

def on_mousebutton_down(target: workspace.Workspace | elements.Scene, mousebutton: state.MouseButtonValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.mousebutton_down(mousebutton, profile), event_func).parent = target
        return event_func
    return wrapper

def on_mousebutton_up(target: workspace.Workspace | elements.Scene, mousebutton: state.MouseButtonValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.mousebutton_up(mousebutton, profile), event_func).parent = target
        return event_func
    return wrapper

def while_mousebutton_held(target: workspace.Workspace | elements.Scene, mousebutton: state.MouseButtonValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.mousebutton_held(mousebutton, profile), event_func).parent = target
        return event_func
    return wrapper

def on_controllerbutton_down(target: workspace.Workspace | elements.Scene, controllerbutton: state.ControllerButtonValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.controllerbutton_down(controllerbutton, profile), event_func).parent = target
        return event_func
    return wrapper

def on_controllerbutton_up(target: workspace.Workspace | elements.Scene, controllerbutton: state.ControllerButtonValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.controllerbutton_up(controllerbutton, profile), event_func).parent = target
        return event_func
    return wrapper

def while_controllerbutton_held(target: workspace.Workspace | elements.Scene, controllerbutton: state.ControllerButtonValue, profile: state.InputProfile | None = None):
    def wrapper(event_func: Callable[[workspace.Workspace], None]):
        Event(lambda w: w.input_state.controllerbutton_held(controllerbutton, profile), event_func).parent = target
        return event_func
    return wrapper
