from __future__ import annotations

from typing import TYPE_CHECKING

import pygame as pg

from ..state import InputState, InputProfile
from ..resources import log, Severity, ControllerConnected, ControllerNotConnected
from ..state import Key, MouseButton, ControllerButton

if TYPE_CHECKING:
    from .workspace import Workspace

class InputManager:
    _forwarded = {
        "state": {
            "rename": "input_state"
        },
        "controller_profiles": {},
        "profile_changes": {},
        "profiles_added": {},
        "profiles_removed": {},
        "bad_joystick_indices": {},
        "get_controller_name": {},
        "rumble_controller": {},
        "stop_rumble_controller": {},
    }

    state: InputState
    controller_profiles: dict[InputProfile, int]

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

        self.state = InputState()
        self.controller_profiles: dict[InputProfile, int] = {} # profile -> instance_id
        self._joysticks: dict[int, pg.joystick.JoystickType] = {} # instance_id -> joystick
        self._profile_changes: list[tuple[InputProfile, bool]] = [] # (profile, is_connected)

        self._profile_added_cached: set[InputProfile] = set() # profiles that have been added to the profile changes list
        self._profile_removed_cached: set[InputProfile] = set() # profiles that have been removed from the profile changes list/
        self._profile_caches_dirty: bool = False # whether the profile caches need to be updated, to prevent redundant cache updates when multiple profiles are added/removed in a single frame

        self._bad_joystick_indices: set[int] = set() # device indices that failed to initialize as joysticks, to send to any higher level logs
        self._create_controller_profiles()


    def clean_profile_caches(self):
        if self._profile_caches_dirty:
            self._profile_added_cached = {profile for profile, is_connected in self._profile_changes if is_connected}
            self._profile_removed_cached = {profile for profile, is_connected in self._profile_changes if not is_connected}
            self._profile_caches_dirty = False

    @property
    def profile_changes(self) -> list[tuple[InputProfile, bool]]:
        return self._profile_changes

    @property
    def profiles_added(self) -> set[InputProfile]:
        self.clean_profile_caches()
        return self._profile_added_cached
    
    @property
    def profiles_removed(self) -> set[InputProfile]:
        self.clean_profile_caches()
        return self._profile_removed_cached
    
    @property
    def bad_joystick_indices(self) -> set[int]:
        return self._bad_joystick_indices
    

    def _try_create_joystick(self, device_index: int) -> pg.joystick.JoystickType | None:
        try:
            joystick = pg.joystick.Joystick(device_index)
            return joystick
        except Exception:
            log(Severity.WARNING, ControllerNotConnected, f"Failed to initialize joystick at device index {device_index}. It will be ignored.")
            self._bad_joystick_indices.add(device_index)
            return None

    def _ensure_controller_profile_state(self, profile: InputProfile):
        self.state.controller_buttons_pressed.setdefault(profile, set())
        self.state.controller_buttons_pressed_last_frame.setdefault(profile, set())
        self.state.controller_left_sticks.setdefault(profile, (0.0, 0.0))
        self.state.controller_right_sticks.setdefault(profile, (0.0, 0.0))
        self.state.controller_left_sticks_last_frame.setdefault(profile, (0.0, 0.0))
        self.state.controller_right_sticks_last_frame.setdefault(profile, (0.0, 0.0))

    def _profile_from_instance_id(self, instance_id: int) -> InputProfile | None:
        for profile, profile_instance_id in self.controller_profiles.items():
            if profile_instance_id == instance_id:
                return profile
        return None
    
    def _create_controller_profiles(self):
        for device_index in range(pg.joystick.get_count()):
            joystick = self._try_create_joystick(device_index)
            if joystick is None: continue
            self._add_controller_profile(joystick.get_instance_id(), joystick)

    def _add_controller_profile(self, instance_id: int, joystick: pg.joystick.JoystickType | None = None):
        existing_profile = self._profile_from_instance_id(instance_id)
        if existing_profile is not None:
            if joystick is not None:
                self._joysticks[instance_id] = joystick
            self._ensure_controller_profile_state(existing_profile)
            return

        # Find lowest unused profile index
        existing_indices = {profile.value for profile in self.controller_profiles}
        new_index = 0
        while new_index in existing_indices:
            new_index += 1
        new_profile = InputProfile(new_index)
        self.controller_profiles[new_profile] = instance_id
        if joystick is not None:
            self._joysticks[instance_id] = joystick
        self._ensure_controller_profile_state(new_profile)
        self._profile_changes.append((new_profile, True))
        log(Severity.INFO, ControllerConnected, f"Controller connected with instance ID {instance_id} assigned to profile {new_profile}.")

    def _remove_controller_profile(self, instance_id: int):
        profile_to_remove = None
        for profile, id in self.controller_profiles.items():
            if id == instance_id:
                profile_to_remove = profile
                break
        if profile_to_remove is not None:
            del self.controller_profiles[profile_to_remove]
            joystick = self._joysticks.pop(instance_id, None)
            if joystick is not None:
                joystick.quit()
            self.state.controller_buttons_pressed.pop(profile_to_remove, None)
            self.state.controller_buttons_pressed_last_frame.pop(profile_to_remove, None)
            self.state.controller_left_sticks.pop(profile_to_remove, None)
            self.state.controller_right_sticks.pop(profile_to_remove, None)
            self.state.controller_left_sticks_last_frame.pop(profile_to_remove, None)
            self.state.controller_right_sticks_last_frame.pop(profile_to_remove, None)
            self._profile_changes.append((profile_to_remove, False))
            log(Severity.INFO, ControllerConnected, f"Controller with instance ID {instance_id} and profile {profile_to_remove} disconnected.")

    def _controller_event_profile(self, event: pg.event.Event) -> InputProfile | None:
        instance_id = getattr(event, "instance_id", getattr(event, "which", None))
        if instance_id is not None:
            profile = self._profile_from_instance_id(instance_id)
            if profile is not None:
                return profile

        device_index = getattr(event, "joy", None)
        if device_index is not None and device_index < pg.joystick.get_count():
            joystick = self._try_create_joystick(device_index)
            if joystick is None: return None
            return self._profile_from_instance_id(joystick.get_instance_id())

        return None
    
    def get_controller_name(self, profile: InputProfile) -> str | None:
        instance_id = self.controller_profiles.get(profile)
        if instance_id is not None:
            joystick = self._joysticks.get(instance_id)
            if joystick is not None:
                return joystick.get_name()
        return None

    def rumble_controller(self, profile: InputProfile, strength: float, duration_ms: int) -> None:
        instance_id = self.controller_profiles.get(profile)
        if instance_id is not None:
            joystick = self._joysticks.get(instance_id)
            if joystick is not None and hasattr(joystick, "rumble"):
                try:
                    joystick.rumble(strength, strength, duration_ms)
                except Exception:
                    log(Severity.WARNING, ControllerNotConnected, f"Failed to rumble controller with profile {profile}. It may have been disconnected.")
                    self._remove_controller_profile(instance_id)

    def stop_rumble_controller(self, profile: InputProfile) -> None:
        instance_id = self.controller_profiles.get(profile)
        if instance_id is not None:
            joystick = self._joysticks.get(instance_id)
            if joystick is not None and hasattr(joystick, "stop_rumble"):
                try:
                    joystick.stop_rumble()
                except Exception:
                    log(Severity.WARNING, ControllerNotConnected, f"Failed to stop rumble on controller with profile {profile}. It may have been disconnected.")
                    self._remove_controller_profile(instance_id)

    def update_input(self):
        self.state.text_input = []
        self.state.mouse_wheel = 0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.state.quit = True
            else:
                self.state.quit = False

            if event.type == pg.VIDEORESIZE:
                self.workspace._display.windowed_size = event.size
                self.workspace._display.size = event.size
                self.workspace._display._resized = True
                self.workspace._display._rebuild_draw_surface()
            
            elif event.type == pg.WINDOWMAXIMIZED:
                self.workspace._display._maxed = True

            elif event.type == pg.KEYDOWN:
                self.state.keys_pressed.add(Key.from_pygame(event.key))
            elif event.type == pg.KEYUP:
                self.state.keys_pressed.discard(Key.from_pygame(event.key))

            elif event.type == pg.MOUSEBUTTONDOWN:
                self.state.mouse_buttons_pressed.add(MouseButton.from_pygame(event.button))
            elif event.type == pg.MOUSEBUTTONUP:
                self.state.mouse_buttons_pressed.discard(MouseButton.from_pygame(event.button))

            elif event.type == pg.JOYBUTTONDOWN or event.type == pg.CONTROLLERBUTTONDOWN:
                profile = self._controller_event_profile(event)
                if profile is not None:
                    self._ensure_controller_profile_state(profile)
                    self.state.controller_buttons_pressed[profile].add(ControllerButton.from_pygame(event.button))
            elif event.type == pg.JOYBUTTONUP or event.type == pg.CONTROLLERBUTTONUP:
                profile = self._controller_event_profile(event)
                if profile is not None:
                    self._ensure_controller_profile_state(profile)
                    self.state.controller_buttons_pressed[profile].discard(ControllerButton.from_pygame(event.button))
            elif event.type == pg.JOYAXISMOTION:
                profile = self._controller_event_profile(event)
                if profile is not None:
                    self._ensure_controller_profile_state(profile)
                    axis = event.axis
                    value = event.value
                    if axis == 0:
                        self.state.controller_left_sticks[profile] = (value, self.state.controller_left_sticks[profile][1])
                    elif axis == 1:
                        self.state.controller_left_sticks[profile] = (self.state.controller_left_sticks[profile][0], value)
                    elif axis == 2:
                        self.state.controller_right_sticks[profile] = (value, self.state.controller_right_sticks[profile][1])
                    elif axis == 3:
                        self.state.controller_right_sticks[profile] = (self.state.controller_right_sticks[profile][0], value)
                    elif axis == 4:
                        if value < -0.5:
                            self.state.controller_buttons_pressed[profile].discard(ControllerButton.LEFTTRIGGER)
                        elif value > 0.5:
                            self.state.controller_buttons_pressed[profile].add(ControllerButton.LEFTTRIGGER)
                    elif axis == 5:
                        if value < -0.5:
                            self.state.controller_buttons_pressed[profile].discard(ControllerButton.RIGHTTRIGGER)
                        elif value > 0.5:
                            self.state.controller_buttons_pressed[profile].add(ControllerButton.RIGHTTRIGGER)

            elif event.type == pg.JOYHATMOTION:
                profile = self._controller_event_profile(event)
                if profile is not None:
                    self._ensure_controller_profile_state(profile)
                    buttons = self.state.controller_buttons_pressed[profile]
                    buttons.discard(ControllerButton.DPAD_UP)
                    buttons.discard(ControllerButton.DPAD_DOWN)
                    buttons.discard(ControllerButton.DPAD_LEFT)
                    buttons.discard(ControllerButton.DPAD_RIGHT)

                    x, y = event.value
                    if x < 0:
                        buttons.add(ControllerButton.DPAD_LEFT)
                    elif x > 0:
                        buttons.add(ControllerButton.DPAD_RIGHT)
                    if y < 0:
                        buttons.add(ControllerButton.DPAD_DOWN)
                    elif y > 0:
                        buttons.add(ControllerButton.DPAD_UP)

            elif event.type == pg.MOUSEMOTION:
                self.state.mouse_pos = event.pos
            elif event.type == pg.TEXTINPUT:
                if event.text:
                    self.state.text_input.append(event.text)
            elif event.type == pg.MOUSEWHEEL:
                self.state.mouse_wheel += event.y

            elif event.type == pg.JOYDEVICEADDED or event.type == pg.CONTROLLERDEVICEADDED:
                device_index = getattr(event, "device_index", getattr(event, "which", None))
                if device_index is not None:
                    joystick = self._try_create_joystick(device_index)
                    if joystick is not None:
                        self._add_controller_profile(joystick.get_instance_id(), joystick)

            elif event.type == pg.JOYDEVICEREMOVED or event.type == pg.CONTROLLERDEVICEREMOVED:
                instance_id = getattr(event, "instance_id", getattr(event, "which", None))
                if instance_id is not None:
                    self._remove_controller_profile(instance_id)


    def next_frame(self, dt: float):
        self.state.next_frame(dt)
        self._profile_changes.clear()
        self._bad_joystick_indices.clear()


__all__ = [
    "InputManager"
]
