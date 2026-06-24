# PlayPy (0.5.0)

PlayPy is a lightweight Python library for creating games, tools, and interactive applications using a retained-mode UI and scene system built on top of pygame. It focuses on rapid prototyping, composable rendering, and simple but powerful layout primitives.

## Requirements

- Python `>=3.11`
- `pygame(-ce) >=2.6.1`

## Installation

```bash
pip install playpy
```

If that does not work:

```bash
python -m pip install playpy
```

---

# Core Concepts

## Module State

Use the following methods to control the state of the module:

```python
plp.init()
plp.quit()
```

---

## Workspace

`Workspace` owns:
- the window
- render loop
- input state
- scene stack
- coroutine scheduler

Key methods:

```python
ws.run()
ws.quit()  # keep in mind that this method calls plp.quit()
ws.wait(seconds)

ws.queue_scene_change(scene)
ws.queue_scene_push(scene)
ws.queue_scene_pop(scene=None)

ws.step()
```

### Scene Scope

Temporarily push a scene using a context manager:

```python
with ws.scene_scope(scene) as (scn, handle):
    ...
```

Call:

```python
handle.disconnect()
```

to remotely pop the scoped scene.

The scoped scene will automatically be disconnected if not disconnected manually.

---

### Screen State
Use `ws.resizable`, `ws.maximized`, and `ws.fullscreen` to check and change current state.
The screen must be resizable to be maximized or fullscreen, and cannot be maximized and fullscreen at the same time.
Use `ws.resized`, `ws.maxed`, and `ws.restored` to check status on current frame.

---

## Layout Values

PlayPy uses two rectangle value types:

### `FRect`:
Relative scale values.

```python
plp.FRect(x, y, w, h)
```

### `Rect`:
Absolute pixel offsets.

```python
plp.Rect(x, y, w, h)
```

---

Final element rectangle:

```text
(scale * parent_size) + offset
```

Helpers:

```python
plp.empty_rect() -> Rect(0, 0, 0, 0)
plp.empty_frect() -> FRect(0, 0, 0, 0)
plp.full_screen_rect() -> (FRect(0, 0, 1, 1), Rect(0, 0, 0, 0))
```

Rect types are iterable and support multiple constructor overloads.

---

## Assets

Assets are reusable wrappers around external files such as images, animations, and sounds.

PlayPy assets load lazily: they store the path when created, then load the underlying pygame resource when needed. You can also call `load()` ahead of time to preload an asset and reduce latency during gameplay.

### Sprites and Animations

`Sprite`s load and store images. Initialize them by passing in a path. (`Path` or `str` object)

`Animation`s store multiple `Sprite`s and allow for changing of animation settings (FPS, loop, etc.)
Pass in either sprite paths (`Path` or `str` object), or `Sprite`s themselves.

### Sounds

`Sound`s load and store user-imported sounds from sound files. Initialize them by passing in a path. (`Path` or `str` object)

Useful methods:
```python
sound = plp.Sound("my_awesome_sound.wav")

sound.load()
sound.play(loop_amt=3, maxtime=10, fade_ms=500)
sound.stop()
sound.set_volume(.5)
volume = sound.get_volume()
```

## Tweening

`Tween`ing is a way to smoothly change values. (like element positions/colors)

`Tween` constructor:
```python
tween = plp.Tween(
    tweened: list[TweenedValue],
    target: list[Any],
    easing_function: TweenEasingFunction | Callable[[float], float] = "cubic",
    easing_style: TweenEasingStyle | None = None,
    length: float = 1,
    looped: bool = False,
    clear_on_finish: bool = True,
)
```

Useful methods/properties include...
```python
tween.looped # whether or not the tween loops
tween.length # the length of the tween
tween.elapsed # the current elapsed time in the tween
tween.finished # whether or not the tween has finished (always false on looped tweens)

tween.edit_easing(function, style) # changes the easing function and style of the tween
tween.play() # plays the tween at the current elapsed time
tween.pause() # stops the tween at the current elapsed time
tween.start() # plays the tween from the start, remapping the start points of the tween to the current values
tween.restart() # plays the tween from the start, reverting the current values of the tween to the start point
tween.stop() # instantly ends the tween; start() must be used to restart a stopped tween.
```

### Handling Tweened Values

`TweenedValue` handles all tweenable values.
```python
val = plp.TweenedValue(
    base_object: object | None,
    key: Any
)
```

`TweenedValue`s support:
- attributes of a class/instance: `TweenedValue(x, "y") = x.y`
- indices/keys of a `list`/`dict`: `TweenedValue(x, y) = x[y]`
- standalone values: `TweenedValue(None, x) = x`.

Useful methods/properties include...
```python
tweened_value.hierarchy_type # returns the hierarchy type (see above) of the TweenedValue ("standalone" / "attribute" / "key" / "index")

tweened_value.get() # gets the current value of the TweenedValue
tweened_value.set(value) # sets the current value of the TweenedValue
```

### Integration Into Workspace

For the tween to update each frame, you must attach it to the workspace.

Active tween helper methods/properties:
```python
ws.active_tweens  # returns all active tweens (cannot be overwritten)

index = ws.add_tween(tween)  # adds a new tween to the workspace and returns it

tween = ws.remove_tween(index)  # removes a tween based on its index and returns it
tween = ws.remove_tween(tween)  # removes a tween and returns it

tween = ws.get_tween(index)  # gets a tween from its index

cleared_tweens = ws.clear_tweens()  # clears all active tweens and returns them
```

---

# Parenting

Any `Element` can contain children.

```python
child.parent = parent
```

or:

```python
parent.add_child(child)
```

Relationship helpers:

```python
is_parent_of()
is_child_of()

is_ancestor_of()
is_descendant_of()
```

Properties:

```python
parent
children
ancestors
descendants
```

---

# Rendering System

PlayPy uses a compositing pipeline.

`Element.draw()` returns a `SurfaceHandler` instead of drawing directly to the workspace.

This enables:
- outlines for arbitrary shapes
- gradients inheriting shape alpha
- subtree compositing
- layered visual effects
- future post-processing support

---

# Elements

## Core Elements

- `Panel`
- `Text`
- `Button`
- `Textbox`
- `Tooltip`
- `Line`
- `Scene`

All elements have the following attributes:

```python
Element(
    scale: FRectValue,  # position/size relative to the parent of the element
    offset: RectValue,  # absolute position/size of the element
    visible: bool = True,  # whether or not this element is visible (processed while drawing) (Tooltip does not have this as it automates visibility)
    enabled: bool = True,  # whether or not this element is enabled (processed when input handling)
    block_input_when_occluded: bool = False,  # whether or not to block the input of this element when it is hovered and another element is hovered above this one
    z: int = 0,  # the z layer of the object
    ignores_environment: bool = False,  # whether or not this element ignores its environment. If an object ignores its environment, it will not obide by its parent's components or child clipping.
)
```

Unless `ignores_environment` is set, elements natively cut off children that are outside of their bounds.

## Effects

`Effect` is a subclass of `Element` that visually modifies its parent subtree.

Built-in effects:

- `Gradient`
- `ButtonGradient`
- `Outline`
- `BorderRadius`
- `VisualLayer`

Effects are ordered using `z`.

Typical layering:

```text
Negative z:
    backgrounds/gradients

Normal z:
    content

Positive z:
    outlines/glows/overlays
```

## Components

`Component`s modify behavior/layout but do not draw.

Built-in components:

- `Padding`
- `Font`
- `Camera`
- `Scrollable`
- `GlobalElement`

Attach/get/remove:

```python
element.set_component(component)

element.get_component(ComponentType)

element.remove_component(ComponentType)
```

or:

```python
component.parent = element
```

---

# Input State

Access input using:

```python
ws.input_state
```

Controller profile changes are tracked on the workspace for the current frame:

```python
ws.profile_changes
ws.profiles_added
ws.profiles_removed
ws.bad_joystick_indices
```

Other miscellaneous controller properties / methods:

```python
ws.get_controller_name(profile)

ws.rumble_controller(profile, strength, duration_ms)
ws.stop_rumble_controller(profile)
```

Properties:

```python
ws.input_state.keys_pressed
ws.input_state.key_downs
ws.input_state.key_ups

ws.input_state.mouse_buttons_pressed
ws.input_state.mouse_downs
ws.input_state.mouse_ups

ws.input_state.mouse_pos
ws.input_state.mouse_delta
ws.input_state.mouse_wheel

ws.input_state.controller_buttons_pressed
ws.input_state.controller_ups
ws.input_state.controller_downs

ws.input_state.controller_left_sticks
ws.input_state.controller_right_sticks
ws.input_state.controller_left_sticks_deltas
ws.input_state.controller_right_stick_deltas

ws.input_state.text_input

ws.input_state.dt
ws.input_state.running_fps
ws.input_state.runtime
ws.input_state.quit
```

Helper m_stateethods:

```pytho_staten
ws.input_state.key_held()
ws.input_state.key_down()
ws.input_state.key_up()

ws.input_state.mousebutton_held()
ws.input_state.mousebutton_down()
ws.input_state.mousebutton_up()

ws.input_state.controllerbutton_held()
ws.input_state.controllerbutton_down()
ws.input_state.controllerbutton_up()

ws.input_state.left_stick(profile)
ws.input_state.right_stick(profile)
ws.input_state.left_stick_delta(profile)
ws.input_state.right_stick_delta(profile)

ws.input_state.input_action_held()
ws.input_state.input_action_down()
ws.input_state.input_action_up()
```

Use `InputAction`s for easier keybind compatibility. Any matching key, mouse button, or controller button can trigger the action.

```python
keybind = plp.InputAction(
    keys = [plp.Key.SPACE, plp.Key.RETURN],
    mouse_buttons = [plp.MouseButton.LEFT],
    controller_buttons = [plp.ControllerButton.A, plp.ControllerButton.B],
    profiles = [plp.InputProfile.KEYBOARD_MOUSE, plp.InputProfile.CONTROLLER_0]
)
```

InputAction event helpers can run handlers directly from those keybinds:

```python
@plp.on_input_action_down(ws, keybind)
def activate(w: plp.Workspace):
    ...

@plp.while_input_action(ws, keybind)
def charge(w: plp.Workspace):
    ...

@plp.on_input_action_up(ws, keybind)
def release(w: plp.Workspace):
    ...
```

Raw input event helpers are available for direct key, mouse button, and controller button checks:

```python
@plp.on_key_down(ws, plp.Key.ESCAPE)
def quit_game(w: plp.Workspace):
    w.quit()

@plp.on_mousebutton_down(ws, plp.MouseButton.LEFT)
def click(w: plp.Workspace):
    ...

@plp.on_controllerbutton_down(ws, plp.ControllerButton.A, plp.InputProfile.CONTROLLER_0)
def confirm(w: plp.Workspace):
    ...
```

---

# Hover State

Workspace hover helpers:

```python
ws.is_mouse_top(element)
ws.is_mouse_over(element)

ws.just_hovered(element)
ws.just_unhovered(element)

ws.just_hovered_inclusive(element)
ws.just_unhovered_inclusive(element)
```

---

# Events

Decorator helpers create `Event` elements.

```python
@plp.on_start(target)
@plp.on_update(target)
@plp.on_quit(target)

@plp.on_resize(target)
@plp.on_maximize(target)
@plp.on_restore(target)

@plp.on_scene_change(target)

@plp.on_profile_changed(target)
@plp.on_profile_added(target)
@plp.on_profile_removed(target)
@plp.on_controller_not_connected(target)

@plp.on_input_action_down(target, action)
@plp.on_input_action_up(target, action)
@plp.while_input_action(target, action)

@plp.on_key_down(target, key, profile=None)
@plp.on_key_up(target, key, profile=None)
@plp.while_key_held(target, key, profile=None)

@plp.on_mousebutton_down(target, mousebutton, profile=None)
@plp.on_mousebutton_up(target, mousebutton, profile=None)
@plp.while_mousebutton_held(target, mousebutton, profile=None)

@plp.on_controllerbutton_down(target, controllerbutton, profile=None)
@plp.on_controllerbutton_up(target, controllerbutton, profile=None)
@plp.while_controllerbutton_held(target, controllerbutton, profile=None)

@on_hover(...)
@on_unhover(...)
@while_hovered(...)

@on_hover_inclusive(...)
@on_unhover_inclusive(...)
@while_hovered_inclusive(...)

@plp.create_event(target, condition)
```

Events attached to the main workspace are global by default.

Example:

```python
@plp.on_update(ws)
def tick(w: plp.Workspace):
    if w.input.key_down(plp.Key.ESCAPE):
        w.quit()
```

---

# Coroutines

Event-like functions can yield.

If a handler returns a generator, PlayPy resumes it on future frames.

Example:

```python
def flash(_: plp.Workspace):
    for _ in range(60):
        print("frame")
        yield
```

Supported in:
- event callbacks
- button callbacks
- textbox callbacks
- other event-like handlers

---

# Textbox Features

`Textbox` supports:
- placeholders
- caret blinking
- text confirmation/reverting
- character filtering
- maximum length
- coroutine callbacks

Useful arguments:

```python
is_char_accepted: Callable[[str], bool] | None,
on_text_updated: Callable[[workspace.Workspace], Generator[None, None, None] | None] | None,
confirm_on_click_off: bool,
```

Special keys:

```text
Backspace -> remove character
Delete    -> clear text
Return    -> confirm text
Escape    -> revert text
```

---

# Scenes

`Scene`s act as "sub-workspaces": when they are alive, only descendants of them (and global elements) are processed and drawn.

Use previously mentioned workspace scene lifecycle methods (`ws.queue_scene_change`, etc.) to manage alive scene.

`Scene`s support lifecycle hooks:

```python
on_enter()
on_exit()
on_pause()
on_resume()
```

Scene changes are queued internally.

---

# Cameras and Scrolling

`Camera` offsets descendant elements.

`Scrollable` extends camera functionality with built-in scrolling support.

Example:

```python
scrollable = plp.Scrollable()
scrollable.parent = panel
```

---

### VisualLayer

`VisualLayer`s render `Sprite`s, `Animation`s, colors, and shader-like effects.

`VisualLayer` constructor:
```python
VisualLayer(
    visual: plp.Sprite | plp.Animation | plp.ColorValue,
    blend_mode: plp.BlendMode | None = None,
    scale: plp.FRectValue = (0, 0, 1, 1),
    offset: plp.RectValue = (0, 0, 0, 0),
    z: int = -1_000_000,
    visible: bool = True,
    ignores_environment: bool = True
)
```

Use the previously mentioned `ignores_environment` for different types of `VisualLayer`s.

```python
# Overlay-style usage:
plp.VisualLayer(sprite, ignores_environment=True)

# Embedded panel/sprite usage:
plp.VisualLayer(sprite, plp.empty_frect(), (20, 20, 50, 50), ignores_environment=False)
```

---

# Logging

PlayPy replaces standard exceptions/logging with a categorized logging system.

```python
plp.log(severity, category, message)
```

Severities:

```python
plp.Severity.INFO
plp.Severity.WARNING
plp.Severity.ERROR
plp.Severity.CRITICAL
```

`ERROR` and `CRITICAL` are treated as `NoReturn`.

Use `plp.enter_debug_mode()` to prevent logs from halting the program.
