from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
import sys
from typing import Self

import pygame as pg

from .rect import CoordinateValue, FCoordinateValue


class _KeyBase(IntEnum):
    def __str__(self) -> str:
        return f"{type(self).__name__}.{self.name}"

    @classmethod
    def from_pygame(cls, value: int | Self) -> Self | int:
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            return value


class Key(_KeyBase):
    DIGIT_0 = pg.K_0
    DIGIT_1 = pg.K_1
    DIGIT_2 = pg.K_2
    DIGIT_3 = pg.K_3
    DIGIT_4 = pg.K_4
    DIGIT_5 = pg.K_5
    DIGIT_6 = pg.K_6
    DIGIT_7 = pg.K_7
    DIGIT_8 = pg.K_8
    DIGIT_9 = pg.K_9
    AC_BACK = pg.K_AC_BACK
    AMPERSAND = pg.K_AMPERSAND
    ASTERISK = pg.K_ASTERISK
    AT = pg.K_AT
    BACKQUOTE = pg.K_BACKQUOTE
    BACKSLASH = pg.K_BACKSLASH
    BACKSPACE = pg.K_BACKSPACE
    BREAK = pg.K_BREAK
    CAPSLOCK = pg.K_CAPSLOCK
    CARET = pg.K_CARET
    CLEAR = pg.K_CLEAR
    COLON = pg.K_COLON
    COMMA = pg.K_COMMA
    CURRENCYSUBUNIT = pg.K_CURRENCYSUBUNIT
    CURRENCYUNIT = pg.K_CURRENCYUNIT
    DELETE = pg.K_DELETE
    DOLLAR = pg.K_DOLLAR
    DOWN = pg.K_DOWN
    END = pg.K_END
    EQUALS = pg.K_EQUALS
    ESCAPE = pg.K_ESCAPE
    EURO = pg.K_EURO
    EXCLAIM = pg.K_EXCLAIM
    F1 = pg.K_F1
    F10 = pg.K_F10
    F11 = pg.K_F11
    F12 = pg.K_F12
    F13 = pg.K_F13
    F14 = pg.K_F14
    F15 = pg.K_F15
    F2 = pg.K_F2
    F3 = pg.K_F3
    F4 = pg.K_F4
    F5 = pg.K_F5
    F6 = pg.K_F6
    F7 = pg.K_F7
    F8 = pg.K_F8
    F9 = pg.K_F9
    GREATER = pg.K_GREATER
    HASH = pg.K_HASH
    HELP = pg.K_HELP
    HOME = pg.K_HOME
    INSERT = pg.K_INSERT
    KP_0 = pg.K_KP0
    KP_1 = pg.K_KP1
    KP_2 = pg.K_KP2
    KP_3 = pg.K_KP3
    KP_4 = pg.K_KP4
    KP_5 = pg.K_KP5
    KP_6 = pg.K_KP6
    KP_7 = pg.K_KP7
    KP_8 = pg.K_KP8
    KP_9 = pg.K_KP9
    KP_DIVIDE = pg.K_KP_DIVIDE
    KP_ENTER = pg.K_KP_ENTER
    KP_EQUALS = pg.K_KP_EQUALS
    KP_MINUS = pg.K_KP_MINUS
    KP_MULTIPLY = pg.K_KP_MULTIPLY
    KP_PERIOD = pg.K_KP_PERIOD
    KP_PLUS = pg.K_KP_PLUS
    LALT = pg.K_LALT
    LCTRL = pg.K_LCTRL
    LEFT = pg.K_LEFT
    LEFTBRACKET = pg.K_LEFTBRACKET
    LEFTPAREN = pg.K_LEFTPAREN
    LESS = pg.K_LESS
    LGUI = pg.K_LGUI
    LMETA = pg.K_LMETA
    LSHIFT = pg.K_LSHIFT
    LSUPER = pg.K_LSUPER
    MENU = pg.K_MENU
    MINUS = pg.K_MINUS
    MODE = pg.K_MODE
    NUMLOCK = pg.K_NUMLOCK
    NUMLOCKCLEAR = pg.K_NUMLOCKCLEAR
    PAGEDOWN = pg.K_PAGEDOWN
    PAGEUP = pg.K_PAGEUP
    PAUSE = pg.K_PAUSE
    PERCENT = pg.K_PERCENT
    PERIOD = pg.K_PERIOD
    PLUS = pg.K_PLUS
    POWER = pg.K_POWER
    PRINT = pg.K_PRINT
    PRINTSCREEN = pg.K_PRINTSCREEN
    QUESTION = pg.K_QUESTION
    QUOTE = pg.K_QUOTE
    QUOTEDBL = pg.K_QUOTEDBL
    RALT = pg.K_RALT
    RCTRL = pg.K_RCTRL
    RETURN = pg.K_RETURN
    RGUI = pg.K_RGUI
    RIGHT = pg.K_RIGHT
    RIGHTBRACKET = pg.K_RIGHTBRACKET
    RIGHTPAREN = pg.K_RIGHTPAREN
    RMETA = pg.K_RMETA
    RSHIFT = pg.K_RSHIFT
    RSUPER = pg.K_RSUPER
    SCROLLLOCK = pg.K_SCROLLLOCK
    SEMICOLON = pg.K_SEMICOLON
    SLASH = pg.K_SLASH
    SPACE = pg.K_SPACE
    SYSREQ = pg.K_SYSREQ
    TAB = pg.K_TAB
    UNDERSCORE = pg.K_UNDERSCORE
    UNKNOWN = pg.K_UNKNOWN
    UP = pg.K_UP
    A = pg.K_a
    B = pg.K_b
    C = pg.K_c
    D = pg.K_d
    E = pg.K_e
    F = pg.K_f
    G = pg.K_g
    H = pg.K_h
    I = pg.K_i
    J = pg.K_j
    K = pg.K_k
    L = pg.K_l
    M = pg.K_m
    N = pg.K_n
    O = pg.K_o
    P = pg.K_p
    Q = pg.K_q
    R = pg.K_r
    S = pg.K_s
    T = pg.K_t
    U = pg.K_u
    V = pg.K_v
    W = pg.K_w
    X = pg.K_x
    Y = pg.K_y
    Z = pg.K_z


class MouseButton(_KeyBase):
    LEFT = pg.BUTTON_LEFT
    MIDDLE = pg.BUTTON_MIDDLE
    RIGHT = pg.BUTTON_RIGHT
    WHEELUP = pg.BUTTON_WHEELUP
    WHEELDOWN = pg.BUTTON_WHEELDOWN
    X1 = pg.BUTTON_X1
    X2 = pg.BUTTON_X2


class ControllerButton(_KeyBase):
    A = pg.CONTROLLER_BUTTON_A
    B = pg.CONTROLLER_BUTTON_B
    X = pg.CONTROLLER_BUTTON_X
    Y = pg.CONTROLLER_BUTTON_Y
    BACK = pg.CONTROLLER_BUTTON_BACK
    GUIDE = pg.CONTROLLER_BUTTON_GUIDE
    START = pg.CONTROLLER_BUTTON_START
    LEFTSTICK = pg.CONTROLLER_BUTTON_LEFTSTICK
    RIGHTSTICK = pg.CONTROLLER_BUTTON_RIGHTSTICK
    LEFTSHOULDER = pg.CONTROLLER_BUTTON_LEFTSHOULDER
    RIGHTSHOULDER = pg.CONTROLLER_BUTTON_RIGHTSHOULDER
    LEFTTRIGGER = pg.CONTROLLER_BUTTON_MAX + 1
    RIGHTTRIGGER = pg.CONTROLLER_BUTTON_MAX + 2
    DPAD_UP = pg.CONTROLLER_BUTTON_DPAD_UP
    DPAD_DOWN = pg.CONTROLLER_BUTTON_DPAD_DOWN
    DPAD_LEFT = pg.CONTROLLER_BUTTON_DPAD_LEFT
    DPAD_RIGHT = pg.CONTROLLER_BUTTON_DPAD_RIGHT


class InputProfile(IntEnum):
    KEYBOARD_MOUSE = -1
    CONTROLLER_0 = 0
    CONTROLLER_1 = 1
    CONTROLLER_2 = 2
    CONTROLLER_3 = 3


KeyValue = Key | int
MouseButtonValue = MouseButton | int
ControllerButtonValue = ControllerButton | int


@dataclass
class InputAction:
    keys: set[KeyValue] = field(default_factory=set)
    mouse_buttons: set[MouseButtonValue] = field(default_factory=set)
    controller_buttons: set[ControllerButtonValue] = field(default_factory=set)
    profiles: set[InputProfile] | None = field(default_factory=set)


class InputState:
    def __init__(self):
        self.keys_pressed: set[KeyValue] = set()
        self.keys_pressed_last_frame: set[KeyValue] = set()
        self.mouse_buttons_pressed: set[MouseButtonValue] = set()
        self.mouse_buttons_pressed_last_frame: set[MouseButtonValue] = set()
        self.controller_buttons_pressed: dict[InputProfile, set[ControllerButtonValue]] = {}
        self.controller_buttons_pressed_last_frame: dict[InputProfile, set[ControllerButtonValue]] = {}
        self.controller_left_sticks: dict[InputProfile, FCoordinateValue] = {}
        self.controller_right_sticks: dict[InputProfile, FCoordinateValue] = {}
        self.controller_left_sticks_last_frame: dict[InputProfile, FCoordinateValue] = {}
        self.controller_right_sticks_last_frame: dict[InputProfile, FCoordinateValue] = {}
        self.mouse_pos: CoordinateValue = (0, 0)
        self.mouse_pos_last_frame: CoordinateValue = (0, 0)
        self.text_input: list[str] = []
        self.mouse_wheel: int = 0

        self.key_downs: set[KeyValue] = set()
        self.mouse_downs: set[MouseButtonValue] = set()
        self.controller_button_downs: dict[InputProfile, set[ControllerButtonValue]] = {}
        self.key_ups: set[KeyValue] = set()
        self.mouse_ups: set[MouseButtonValue] = set()
        self.controller_button_ups: dict[InputProfile, set[ControllerButtonValue]] = {}

        self.mouse_delta: tuple[float, float] = (0.0, 0.0)
        self.controller_left_stick_deltas: dict[InputProfile, tuple[float, float]] = {}
        self.controller_right_stick_deltas: dict[InputProfile, tuple[float, float]] = {}

        self.runtime: float = 0.0
        self.dt: float = 0.0
        self.running_fps: int = sys.maxsize
        self.quit = False

    def next_frame(self, dt: float):
        self.key_downs = self.keys_pressed - self.keys_pressed_last_frame
        self.mouse_downs = self.mouse_buttons_pressed - self.mouse_buttons_pressed_last_frame
        self.controller_button_downs = {profile: buttons - self.controller_buttons_pressed_last_frame.get(profile, set()) for profile, buttons in self.controller_buttons_pressed.items()}
        self.key_ups = self.keys_pressed_last_frame - self.keys_pressed
        self.mouse_ups = self.mouse_buttons_pressed_last_frame - self.mouse_buttons_pressed
        self.controller_button_ups = {profile: self.controller_buttons_pressed_last_frame.get(profile, set()) - buttons for profile, buttons in self.controller_buttons_pressed.items()}
        
        self.mouse_delta = (self.mouse_pos[0] - self.mouse_pos_last_frame[0], self.mouse_pos[1] - self.mouse_pos_last_frame[1])
        zero_pos: tuple[float, float] = (0.0, 0.0)
        self.controller_left_stick_deltas = {
            profile: (
                self.controller_left_sticks.get(profile, zero_pos)[0] - self.controller_left_sticks_last_frame.get(profile, zero_pos)[0],
                self.controller_left_sticks.get(profile, zero_pos)[1] - self.controller_left_sticks_last_frame.get(profile, zero_pos)[1],
            )
            for profile in set(self.controller_left_sticks.keys()) | set(self.controller_left_sticks_last_frame.keys())
        }
        self.controller_right_stick_deltas = {
            profile: (
                self.controller_right_sticks.get(profile, zero_pos)[0] - self.controller_right_sticks_last_frame.get(profile, zero_pos)[0],
                self.controller_right_sticks.get(profile, zero_pos)[1] - self.controller_right_sticks_last_frame.get(profile, zero_pos)[1],
            )
            for profile in set(self.controller_right_sticks.keys()) | set(self.controller_right_sticks_last_frame.keys())
        }

        if self.keys_pressed_last_frame != self.keys_pressed:
            self.keys_pressed_last_frame = self.keys_pressed.copy()
        if self.mouse_buttons_pressed_last_frame != self.mouse_buttons_pressed:
            self.mouse_buttons_pressed_last_frame = self.mouse_buttons_pressed.copy()
        if self.controller_buttons_pressed_last_frame != self.controller_buttons_pressed:
            self.controller_buttons_pressed_last_frame = {profile: buttons.copy() for profile, buttons in self.controller_buttons_pressed.items()}
        if self.controller_left_sticks_last_frame != self.controller_left_sticks:
            self.controller_left_sticks_last_frame = self.controller_left_sticks.copy()
        if self.controller_right_sticks_last_frame != self.controller_right_sticks:
            self.controller_right_sticks_last_frame = self.controller_right_sticks.copy()
        if self.mouse_pos_last_frame != self.mouse_pos:
            self.mouse_pos_last_frame = self.mouse_pos

        self.dt = dt
        self.running_fps = int(1 // dt) if dt > 0 else sys.maxsize
        self.runtime += dt
        self.quit = False
    

    def key_held(self, key: KeyValue, profile: InputProfile | None = None) -> bool:
        if profile is not None and profile is not InputProfile.KEYBOARD_MOUSE:
            return False
        return key in self.keys_pressed
    
    def key_up(self, key: KeyValue, profile: InputProfile | None = None) -> bool:
        if profile is not None and profile is not InputProfile.KEYBOARD_MOUSE:
            return False
        return key in self.key_ups
    
    def key_down(self, key: KeyValue, profile: InputProfile | None = None) -> bool:
        if profile is not None and profile is not InputProfile.KEYBOARD_MOUSE:
            return False
        return key in self.key_downs


    def mousebutton_held(self, mousebutton: MouseButtonValue, profile: InputProfile | None = None) -> bool:
        if profile is not None and profile is not InputProfile.KEYBOARD_MOUSE:
            return False
        return mousebutton in self.mouse_buttons_pressed
    
    def mousebutton_up(self, mousebutton: MouseButtonValue, profile: InputProfile | None = None) -> bool:
        if profile is not None and profile is not InputProfile.KEYBOARD_MOUSE:
            return False
        return mousebutton in self.mouse_ups
    
    def mousebutton_down(self, mousebutton: MouseButtonValue, profile: InputProfile | None = None) -> bool:
        if profile is not None and profile is not InputProfile.KEYBOARD_MOUSE:
            return False
        return mousebutton in self.mouse_downs
    
    
    def controllerbutton_held(self, controllerbutton: ControllerButtonValue, profile: InputProfile | None) -> bool:
        if profile is not None and profile is InputProfile.KEYBOARD_MOUSE:
            return False
        if profile is None:
            return any(controllerbutton in buttons for buttons in self.controller_buttons_pressed.values())
        return controllerbutton in self.controller_buttons_pressed.get(profile, set())
    
    def controllerbutton_up(self, controllerbutton: ControllerButtonValue, profile: InputProfile | None) -> bool:
        if profile is not None and profile is InputProfile.KEYBOARD_MOUSE:
            return False
        if profile is None:
            return any(controllerbutton in buttons for buttons in self.controller_button_ups.values())
        return controllerbutton in self.controller_button_ups.get(profile, set())
    
    def controllerbutton_down(self, controllerbutton: ControllerButtonValue, profile: InputProfile | None) -> bool:
        if profile is not None and profile is InputProfile.KEYBOARD_MOUSE:
            return False
        if profile is None:
            return any(controllerbutton in buttons for buttons in self.controller_button_downs.values())
        return controllerbutton in self.controller_button_downs.get(profile, set())


    def input_action_held(self, action: InputAction) -> bool:
        for profile in action.profiles or {None}:
            if any(self.key_held(key, profile) for key in action.keys):
                return True
            if any(self.mousebutton_held(mousebutton, profile) for mousebutton in action.mouse_buttons):
                return True
            if any(self.controllerbutton_held(controllerbutton, profile) for controllerbutton in action.controller_buttons):
                return True
        return False
    
    def input_action_up(self, action: InputAction) -> bool:
        for profile in action.profiles or {None}:
            if any(self.key_up(key, profile) for key in action.keys):
                return True
            if any(self.mousebutton_up(mousebutton, profile) for mousebutton in action.mouse_buttons):
                return True
            if any(self.controllerbutton_up(controllerbutton, profile) for controllerbutton in action.controller_buttons):
                return True
        return False
    
    def input_action_down(self, action: InputAction) -> bool:
        for profile in action.profiles or {None}:
            if any(self.key_down(key, profile) for key in action.keys):
                return True
            if any(self.mousebutton_down(mousebutton, profile) for mousebutton in action.mouse_buttons):
                return True
            if any(self.controllerbutton_down(controllerbutton, profile) for controllerbutton in action.controller_buttons):
                return True
        return False


__all__ = [
    "Key",
    "MouseButton",
    "ControllerButton",
    "InputProfile",
    "KeyValue",
    "MouseButtonValue",
    "ControllerButtonValue",
    "InputAction",
    "InputState",
]
