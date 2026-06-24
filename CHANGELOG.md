# Changelog

## [0.6.0] - ???

### Added

- Added `FRect` functionality to multiply by `int`s.

### Fixed

- Fixed some outdated / misleading information in `README.md`

## [0.5.0] - 20 June 2026

### Added

- Added pygane controller error guards so that one bad joystick does not crash the whole app, instead it raises a warning and gets added to the `bad_joystick_indices` set.
- Added `ws.toggle_mouse_visible()` and `ws.mouse_visible`.
- Added `Workspace` fullscreen / maximization / resizability support.
    - Added `ws.resizable`, `ws.maximized`, and `ws.fullscreen` to check and change current state.
    - Added `ws.resized`, `ws.maxed`, and `ws.restored` to check status on current frame.
        - Added event helpers: `@plp.on_resize`, `@plp.on_maximize`, and `@plp.on_restore`.
- Added `ws.get_controller_name()`, `ws.rumble_controller()`, and `ws.stop_rumble_controller()`.
- Added `InputAction` event helpers: `@plp.on_input_action_down`, `@plp.on_input_action_up`, and `@plp.while_input_action`.
- Added raw key, mouse button, and controller button event helpers for down/up/held input checks.
- Added `InputState.running_fps`, which is the FPS of the current frame (`1 // dt`).
- Added `Tooltip`, which is a naturally `ignor`ing`_environment` `Panel` that automates visibility to when it or its parent is hovered.
- Added `Tween`s and `TweenedValue`s and integrated them into the workspace.
- Added functionality for `Rect`s and `FRect`s to add and multiply. (`Rect + Rect`, `Rect * Rect | int`, `FRect + FRect`, `FRect * FRect | float`)

### Changed

- Made input and draw orders cached and only update when child z orders are updated.
- Made `SurfaceHandler.extend()` only create a new union surface if `clip_within_self` is set to `True` **and** the other surface that it is being extended by is larger than the current surface.
- Changed `ignores_environment` from a class attribute to an instance attribute, so that some effect (like image `VisualLayer`s and `Tooltip`s) can change this value without it affecting the whole class.
- Segmented `Workspace` processes for cleaner code and easier editing. (`Workspace` now contains `DisplayManager`, `InputManager`, and other classes that provide function for `Workspace` itself)
- Made event helpers return the event function they took in so that the event function can be used outside of the actual event.
- Allowed and defaulted `VisualLayer` to take in `blend_mode = None`.
- Updated `workspace/` so that `workspace.py` dynamically creates facades, making it easier to navagate the workspace submodule.
- Moved workspace hierarchy logic to `core/workspace/element_hierarchy.py`.

### Fixed

- Fixed `enter_debug_mode()` not actually setting `_debug`
- Fixed `Textbox` unfocusing on click even if already unfocused.

### Removed

- Removed `ws.input` (now `ws.input_state`).

## [0.4.0] - 24 May 2026

### Added

- Added `ws.profile_changes` (`ws.profiles_added` and `ws.profiles_removed`); list of every profile connect/disconnect on the current frame.
    - Added event helpers: `@plp.on_profile_changed`, `@plp.on_profile_added`, `@plp.on_profile_removed`.
- Added `InputAction`; keybind helper.
- Added `InputProfile`; represents the controller/keyboard that was used to make the input. (`KEYBOARD_MOUSE` / `CONTROLLER_0-3`)
- Added `ControllerButton` and `ControllerButtonValue`. (Usable in `InputState`)
- Added `Sound`; lazily loads and plays sounds.
    - Lazy loading uses an internal cache that stores already used paths and retrieves sounds from the cache when a cached sound is loaded.
- Added `Workspace.wait(seconds)`; waits while stepping the workspace when possible.

### Changed

- Updated `Sprite` to use the same lazy loading pattern as `Sound`.
- Updated `README` to show information about `VisualLayer`.

### Fixed

- Fixed `_resolve_queued_scene_change()` incorrectly using `_scene_changed` to detect queued scene changes, which could cause scene changes queued during input callbacks to be skipped.
- Fixed `Sprite` and `Animation` not being in `plp.__all__`.
- Fixed `Line.flipped` being set to `False` in `__init__()` despite the value passed in to it.
- Fixed `InputAction` requiring every input group to match instead of accepting any matching key, mouse button, or controller button.
- Fixed controller button detection by supporting both pygame controller button events and raw joystick button events.
- Fixed controller trigger button values aliasing d-pad button values.
- Fixed pygame discarding joysticks by manually saving them and calling `joystick.quit()` when they are disconnected.
- Fixed raw joystick d-pad input by mapping `JOYHATMOTION` to `ControllerButton.DPAD_*`.

### Removed

- Removed `scene_changed` being set when the scene change is first queued.
- Removed `plp.core.workspace.init()` as it was redundant and was already implemented through `plp.core.resources.init()`

## [0.3.1] - 23 May 2026

### Changed

- Made `Element`s with `ignores_environment = True` ignore `Camera` and `Scrollable` offsets.

### Fixed

- Fixed `Scrollable` `Panel`s with `Padding` incorrectly padding children that were within the scrollable content range but outside the panel's visible bounds.
- Fixed scroll direction on `Scrollable` `Panel`s.

## [0.3.0] - 23 May 2026

### Added

- Added `Element` `Line`; creates a line from the topleft of the object to the bottomright (topright to bottomleft if `flipped = true`).
    - Changed `Textbox` to use this object instead of the native `pg.draw.line()` function.
- Added `Element.ignores_environment` (`False` for all elements except `Effect`s); `Element`s with this flag check will not be affected by padding, will expand past the bounds of their parents, and do not appear in the hover stack.
- Added coroutines; when yielding in `handle_input()` or any other event-like function, waits until the next frame before entering back into the function.
- Added `Workspace.scene_scope()`; `contextmanager` that pushes the scene on entrance, and pops it on exit.
    - Should be used as `with ws.scene_scope(scene_obj) as (scn, handle):`
- Added `Modifier` `Camera`; offsets children of the attached element by the camera deltas.
    - Switched out `scrollable: bool` on `Panel`s with `Modifier` `Scrollable`, which acts the same as `Camera`, but has built-in methods for scrolling and is wired directly in to `Panel`.
- Added more key functions to `UITextbox`:
    - Pressing `Delete` deletes the entire text.
    - Pressing `Return` confirms the change in text.
    - Pressing `Esc` reverts the text to how it was before it was selected.
- Added arguments to `UITextbox`:
    - `is_char_accepted`: Function that returns whether or not the provided character is valid in the textbox.
    - `on_text_updated`: Function that is called when the textbox text is updated. (Will only be called when the text is confirmed on unfocusing)
    - `confirm_on_click_off`: Denotes whether or not the text will confirm the change in the text when the textbox is clicked off.
- Added `Workspace().step()`; completes one frame of the main run process.
- Added `frames_back` argument to `log()`; sets how many frames to backtrack to get the frame that started the log (starting from the frame that called `log()`).
- Added `UIModifier` `ButtonGradient`. (`UIButton` compatible `UIGradient`)
- Added `full_screen_rect()`. (Returns `(FRect(0, 0, 1, 1), empty_rect())`)

### Changed

- Completely removed `Modifier`, replacing it with `Component` which is just a rename (`Padding`, `Font`, `GlobalElement`, `Camera`, and `Scrollable` all stayed in this category), and `Effect` which is a subclass of `Element` that applies a visual effect to the parent `Element` (all other `Modifier`s moved to this category).
- Changed how `Element.draw()` works, opening possibilities to more rendering capabilities.
- Removed `UI` prefix from all class names.
- Made scene pops require a specific scene to be popped.
    - `queue_scene/modal_pop()` both take `None` as a default argument; when `None` is provided, they will take the active scene/modal.
- Made `log(Severity.ERROR/Severity.CRITICAL)` show up as returning `NoReturn`.
- Cleaned up `Rect`/`FRect` constructor code.
- Made `Rect` and `FRect` iterable.
- Changed order in `run`. (scene resolution was between input updating and handling, moved it to the start of the loop)
- Made quit value resetting instant.
- Made it so that rect values can be passed into `UIElement`s instead of strictly `FRect`/`Rect`.

### Fixed

- Fixed caret position in `UITextbox`; it used to be on the right edge of the entire textbox.
- Fixed `UIPadding` padding even when no padding is needed.
- Fixed `UIPadding` padding the element itself instead of its children.
- Fixed `generate_global_processing_order()` adding base level elements to the order twice.

### Removed

- Removed modals as they can be replicated mostly by scenes and were very buggy.
- Removed `UIScrollablePanel`. (`UIPanel` already has its functionality)

## [0.2.1] - 18 May 2026

### Added

- Added **Hover State** to the **Input State** category in `README`.
    - Added some helper methods for checking hover state.
    - Also added event helpers for the same checks.
- Added properties and functions to the `InputState` class.
- Added the `README` to `__init__.py`.

### Changed

- Moved **Version-Specific Details** to the `CHANGELOG`.

### Fixed

- Fixed some typos in the `README`.
- Fixed a bug in the modal stack popping where the popped modal would report a change even if it was not the top modal.

## [0.2.0] - 25 Apr 2026

### Added

- Added `GlobalElement` `UIModifier`.
    - If you add this to an element and make it a descendant of `Workspace`, it will be drawn and handled even when a `Scene` is being run.
    - **Global** `UIElements` are processed last if a scene is opened and they are on the `Workspace`.
- `Events` have a new property: `global_event` (default `True`).
    - If `global_event` is enabled when creating the event, it will be given the `GlobalElement` modifier and be global.
- Made scene changes and modal changes queued.
    - You can now use methods `queue_scene_change(scene)`, `queue_scene_push(scene)`, `queue_scene_pop()`, `queue_modal_push(element)`, and `queue_modal_pop(element)` to manage scenes and modals.
- Added `RectValue`, `FRectValue`, `CoordinateValue`, and `FCoordinateValue` as types for coordinates and rectangles. `Rect` and `FRect` now control rectangle values.
- Added properties and methods to `UIElement` for helping with descendants and ancestors.
- Replaced Python's normal error system with logging, allowing for warnings and info logs.
    - Use the `plp.log(severity, category, message)` function to log.
    - Severities come from `plp.Severity`. (`INFO`, `WARNING`, `ERROR`, `CRITICAL`)
    - Categories come from children of the `plp.Log` class.

### Changed

- Switched out the `plp.pg` calls for a `Key` enum to access keys.
- `Scene`s now crop descendant elements that extend outside the scene bounds, including hit-testing.

### Removed

- Removed `del element.parent` and replaced it with `element.destroy()`.

# Version-Specific Details

- **<1.0.0** - All versions in this range will not use deprecation and instead will just have old methods removed.
