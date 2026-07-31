from __future__ import annotations

import os
from typing import Literal, NoReturn, overload

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"


import inspect
import sys
from pathlib import Path
from enum import Enum, auto

import pygame as pg
import colorama as clr

clr.init()

__version__ = "0.5.0"

DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_ICON_PATH = DATA_DIR / "default_icon.ppm"

_init_message = (
    clr.Style.BRIGHT + f"Hello from PlayPy! (V{__version__})\n" +
    clr.Style.DIM + f"    Pygame V{pg.version.ver}\n" +
    clr.Style.NORMAL + clr.Fore.YELLOW + "    [WARNING]: This package is a beta. Things will be changed, and bugs might appear.\n" +
    clr.Style.RESET_ALL + "PlayPy is a lightweight Python library for creating games, tools, and interactive applications using a retained-mode UI and scene system built on top of pygame. It focuses on rapid prototyping, composable rendering, and simple but powerful layout primitives."
)

_initialized = False
_debug = False
_detailed_debug = False

def enter_debug_mode(detailed: bool = False):
    global _debug, _detailed_debug
    if _initialized:
        log(Severity.ERROR, InitializationError, 'Please use "enter_debug_mode" before all other methods as it cannot be used after initialization.')
    _debug = True
    if detailed:
        _detailed_debug = True

def init():
    global _initialized
    if not _initialized:
        pg.init()
        _initialized = True
        if _init_message:
            print(_init_message)

def quit():
    global _initialized
    if _initialized:
        pg.quit()
        _initialized = False

def require_init():
    if not _initialized:
        log(Severity.WARNING, InitializationWarning, "Please call the `plp.init()` function before doing anything else in this module.", frames_back=2)
        init()

class Log: pass
class LogWarning(Log): pass
class LogError(Log): pass

class InitializationError(LogError): pass
class InitializationWarning(LogWarning): pass
class InvalidDirectory(LogError): pass
class InvalidValue(LogError): pass
class ControllerConnected(Log): pass
class ControllerNotConnected(LogWarning): pass
class MissingAttribute(LogError): pass

class Severity(Enum):
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

sev_color: dict[Severity, str] = {
    Severity.INFO: clr.Fore.BLUE,
    Severity.WARNING: clr.Fore.YELLOW,
    Severity.ERROR: clr.Fore.RED,
    Severity.CRITICAL: clr.Style.BRIGHT + clr.Fore.RED
}

sev_stack_size: dict[Severity, int | None] = {
    Severity.INFO: 0,
    Severity.WARNING: 3,
    Severity.ERROR: 5,
    Severity.CRITICAL: None
}

no_stack_error_type = InvalidDirectory

def no_stack_error(log_category: type[Log], prev_frame: inspect.FrameInfo | None = None):
    print(
        f"{sev_color[Severity.CRITICAL]}[CRITICAL]: {prev_frame.filename + ':' + str(prev_frame.lineno) if prev_frame else '<Location not found>'}\n" +
        f"  [{no_stack_error_type.__name__}]: Could not print [{log_category.__name__}] log as the current stack was not found.{clr.Style.RESET_ALL}"
    )
    sys.exit(1)

@overload
def log(severity: Literal[Severity.ERROR, Severity.CRITICAL], /, category: type[Log], message: str, *, frames_back: int = 0) -> NoReturn: ...

@overload
def log(severity: Literal[Severity.INFO, Severity.WARNING], /, category: type[Log], message: str, *, frames_back: int = 0) -> None: ...

def log(severity: Severity, /, category: type[Log], message: str, *, frames_back: int = 0):
    full_msg: str = ""

    current_frame = inspect.currentframe()
    if not current_frame:
        no_stack_error(category)
        return
    for _ in range(frames_back + 1):
        current_frame = current_frame.f_back
        if not current_frame:
            no_stack_error(category)
            return
    
    warn_info = inspect.getframeinfo(current_frame)

    full_msg += f"{sev_color[severity]}[{severity.name}] In {warn_info.filename}, line {warn_info.lineno}\n"

    if severity != Severity.CRITICAL:
        full_msg += clr.Style.RESET_ALL

    full_msg += f"  [{category.__name__}]: {message}\n"

    full_msg += clr.Style.RESET_ALL + clr.Style.DIM

    stack_left = sev_stack_size[severity]

    while current_frame and (stack_left is None or stack_left > 0):
        info = inspect.getframeinfo(current_frame)
        if "importlib" in info.filename:
            current_frame = current_frame.f_back
            continue
        full_msg += f"    {info.filename}:{info.lineno}{'\n      ' + info.code_context[0].strip() if info.code_context else ''}\n"
        current_frame = current_frame.f_back
        if stack_left is not None:
            stack_left -= 1

    full_msg += clr.Style.RESET_ALL

    print(full_msg)

    if (severity == Severity.ERROR or severity == Severity.CRITICAL) and not _debug:
        sys.exit(1)

def _make_surface(size: tuple[int, int]):
    return pg.Surface(size, pg.SRCALPHA)

__all__ = [
    "DATA_DIR",
    "DEFAULT_ICON_PATH",
    "__version__",
    "enter_debug_mode",
    "init",
    "quit",
    "Log",
    "LogWarning",
    "LogError",
    "InitializationError",
    "InitializationWarning",
    "InvalidDirectory",
    "InvalidValue",
    "ControllerConnected",
    "ControllerNotConnected",
    "MissingAttribute",
    "Severity",
    "log",
    "_make_surface"
]
