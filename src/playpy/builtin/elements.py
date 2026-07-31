from collections import deque
from collections.abc import Callable, Generator
from typing import Literal

import pygame as pg
import textwrap

from ..core import state
from ..core import elements
from ..core import workspace
from ..core import resources

from .components import Font, Scrollable, Padding


__all__ = [
    "Panel",
    "Line",
    "TextAlign",
    "Text",
    "Button",
    "Textbox",
    "Tooltip",
]

class Panel(elements.Element):
    def __init__(
        self,
        scale: state.FRectValue,
        offset: state.RectValue,
        color: state.ColorValue,
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = False,
        max_scroll_scale: float | None = None,
        max_scroll_offset: int = 0,
    ):
        super().__init__(scale, offset, visible, enabled, False, z, ignores_environment)
        self.color = color
        self._max_scroll_scale = max_scroll_scale
        self.max_scroll_offset = max_scroll_offset
        
        self._covering_children_dirty: bool = False
        self._covering_children: list[elements.Element] = []

    def _propagate_visual_change(self, order: bool = False, ancestors_handled: bool = False):
        self._covering_children_dirty = True
        super()._propagate_visual_change(order)

    def max_scroll_scale_x(self, workspace: workspace.Workspace) -> float:
        if self._max_scroll_scale is not None:
            return self._max_scroll_scale
        def key(c):
            if isinstance(c, elements.Element):
                return c.scale.right
            return 0
        if self.children:
            right_children = max(key(child) for child in self.children)
            if padding_comp := self.get_component(Padding): right_children += padding_comp.scale
            return max(0, right_children - 1)
        return 0

    def max_scroll_scale_y(self, workspace: workspace.Workspace) -> float:
        if self._max_scroll_scale is not None:
            return self._max_scroll_scale
        def key(c):
            if isinstance(c, elements.Element):
                return c.scale.bottom
            return 0
        if self.children:
            bottom_children = max(key(child) for child in self.children)
            if padding_comp := self.get_component(Padding): bottom_children += padding_comp.scale
            return max(0, bottom_children - 1)
        return 0
    
    def _update_covering_children(self):
        found_covering: list[elements.Element] = []
        queue: deque[elements.Element] = deque(self.children)

        while queue:
            current = queue.popleft()
            if isinstance(current, Panel):
                found_covering.append(current)
                continue
            queue.extend(current.children)

        self._covering_children = found_covering
        self._covering_children_dirty = False

    def _hovered_and_no_covering(self, workspace: workspace.Workspace):
        return workspace.is_mouse_over(self) and not any(workspace.is_mouse_over(child) for child in self._covering_children)

    def handle_input(self, workspace: workspace.Workspace):
        if self._covering_children_dirty:
            self._update_covering_children()
        scroll_comp = self.get_component(Scrollable)
        if scroll_comp is None:
            return
        if self._hovered_and_no_covering(workspace):
            if workspace.input_state.mouse_wheel != 0:
                max_offset = self.max_scroll_offset
                if padding_comp := self.get_component(Padding): max_offset += padding_comp.offset
                panel_rect = workspace.get_element_rect(self)
                if workspace.input_state.key_down(state.Key.LSHIFT) or workspace.input_state.key_down(state.Key.RSHIFT):
                    max_scale = self.max_scroll_scale_x(workspace)
                    max_scroll = panel_rect.w * max_scale + max_offset
                    scroll_comp.scroll_x(workspace.input_state.mouse_wheel, 0, round(max_scroll))
                else:
                    max_scale = self.max_scroll_scale_y(workspace)
                    max_scroll = panel_rect.h * max_scale + max_offset
                    scroll_comp.scroll_y(workspace.input_state.mouse_wheel, 0, round(max_scroll))
                self._propagate_layout_change(updates_children=True)

    def draw(self, workspace: "workspace.Workspace", current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler:
        rect = workspace.get_element_rect(self)
        surf = resources._make_surface(rect.size)
        surf.fill(self.color)
        return state.SurfaceHandler(surf, rect.topleft)
    
class Line(elements.Element):
    def __init__(
        self,
        scale: state.FRectValue,
        offset: state.RectValue,
        color: state.ColorValue,
        width: int = 1,
        flipped: bool = False,
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = False,
    ):
        super().__init__(scale, offset, visible, enabled, z=z, ignores_environment=ignores_environment)
        self.color = color
        self.width = width
        self.flipped = flipped

    def handle_input(self, workspace: elements.Workspace) -> None:
        return
    
    def updated_pos(self, workspace: elements.Workspace, current_surface: state.SurfaceHandler | None) -> tuple[int, int]:
        rect = workspace.get_element_rect(self)
        return (rect.x - self.width, rect.y - self.width)

    def draw(self, workspace: elements.Workspace, current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler:
        rect = workspace.get_element_rect(self)
        size = (rect.w + self.width * 2, rect.h + self.width * 2)
        surf = resources._make_surface(size)
        pos = (rect.x - self.width, rect.y - self.width)
        if self.flipped:
            point1, point2 = (rect.w + self.width, self.width), (self.width, rect.h + self.width)
        else:
            point1, point2 = (self.width, self.width), (rect.w + self.width, rect.h + self.width)
        pg.draw.line(surf, self.color, point1, point2, self.width)
        return state.SurfaceHandler(surf, pos)

TextAlign = Literal[
    "topleft", "topright", "midtop",
    "midleft", "midright", "center",
    "bottomleft", "bottomright", "midbottom",
]

def _wrap_text_to_width(font: pg.font.Font, text: str, max_width: int) -> list[str]:
    if max_width <= 0:
        return text.splitlines() if text else [""]
    lines: list[str] = []
    for raw_line in text.splitlines() or [""]:
        if raw_line == "":
            lines.append("")
            continue
        words = raw_line.split(" ")
        current = ""
        for word in words:
            candidate = word if current == "" else f"{current} {word}"
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                # If a single word is too long, hard-wrap it.
                if font.size(word)[0] > max_width:
                    # rough wrap by characters, then refine with font size
                    approx = textwrap.wrap(word, width=max(1, int(len(word) * max_width / max(font.size(word)[0], 1))))
                    for chunk in approx[:-1]:
                        lines.append(chunk)
                    current = approx[-1] if approx else ""
                else:
                    current = word
        lines.append(current)
    return lines

class Text(elements.Element):
    def __init__(
        self,
        scale: state.FRectValue,
        offset: state.RectValue,
        text: str,
        color: state.ColorValue = (0, 0, 0),
        align: TextAlign = "topleft",
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = False,
    ):
        super().__init__(scale, offset, visible, enabled, z=z, ignores_environment=ignores_environment)
        self.text = text
        self.color = color
        self.align = align

    def _get_font(self) -> tuple[pg.Font, bool]:
        font_comp = self.get_component(Font)
        font_path = None
        font_size = 24
        bold = False
        italic = False
        antialias = True

        if font_comp is not None:
            if font_comp.font_path is not None:
                font_path = font_comp.font_path
            if font_comp.font_size is not None:
                font_size = font_comp.font_size
            if font_comp.bold is not None:
                bold = font_comp.bold
            if font_comp.italic is not None:
                italic = font_comp.italic
            if font_comp.antialias is not None:
                antialias = font_comp.antialias

        font = pg.font.Font(font_path, font_size)
        font.set_bold(bold)
        font.set_italic(italic)

        return font, antialias

    def _get_base_text_pos(self, workspace: workspace.Workspace, num_lines: int) -> tuple[int, int]:
        font, _ = self._get_font()

        line_h = font.get_linesize()
        block_h = line_h * num_lines

        rect = workspace.get_element_rect(self)

        # Determine starting position based on alignment
        if "top" in self.align:
            start_y = rect.y
        elif "bottom" in self.align:
            start_y = rect.bottom - block_h
        else:
            start_y = rect.centery - block_h // 2

        if "left" in self.align:
            start_x = rect.x
        elif "right" in self.align:
            start_x = rect.right
        else:
            start_x = rect.centerx
        return start_x, start_y

    def _get_lines(self, workspace: workspace.Workspace) -> list[tuple[pg.Surface, pg.Rect]]:
        font, antialias = self._get_font()

        rect = workspace.get_element_rect(self)
        lines = _wrap_text_to_width(font, self.text, rect.w)
        line_h = font.get_linesize()

        start_x, start_y = self._get_base_text_pos(workspace, len(lines))

        text_specs: list[tuple[pg.Surface, pg.Rect]] = []
        for i, line in enumerate(lines):
            surface = font.render(line, antialias, self.color)
            text_rect = surface.get_rect()
            if "left" in self.align:
                text_rect.x = start_x
            elif "right" in self.align:
                text_rect.right = start_x
            else:
                text_rect.centerx = start_x
            text_rect.y = start_y + i * line_h

            text_specs.append((surface, text_rect))
        return text_specs

    def updated_pos(self, workspace: elements.Workspace, current_surface: state.SurfaceHandler | None) -> state.CoordinateValue | None:
        text_specs = self._get_lines(workspace)
        if not text_specs:
            return
        return text_specs[0][1].topleft

    def draw(self, workspace: workspace.Workspace, current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler | None:
        text_specs = self._get_lines(workspace)
        if not text_specs:
            return
        rects = [rect for _, rect in text_specs]
        full_rect = pg.Rect(rects[0].topleft, (max(rect.w for rect in rects), sum(rect.h for rect in rects)))
        surf = resources._make_surface(full_rect.size)
        for text_surf, rect in text_specs:
            pos = (rect.x - full_rect.x, rect.y - full_rect.y)
            surf.blit(text_surf, pos)
        return state.SurfaceHandler(surf, full_rect.topleft)

    def handle_input(self, workspace: workspace.Workspace):
        pass

class Button(Panel):
    def __init__(
        self,
        scale: state.FRectValue,
        offset: state.RectValue,
        text: str,
        on_click: Callable[
            [workspace.Workspace],
            Generator[None, None, None] | None
        ] | None = None,
        color: state.ColorValue = (200, 200, 200),
        hover_color: state.ColorValue | None = None,
        pressed_color: state.ColorValue | None = None,
        text_color: state.ColorValue = (0, 0, 0),
        font_path: str | None = None,
        font_size: int = 24,
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = False,
    ):
        super().__init__(scale, offset, color, visible, enabled, z, ignores_environment)
        self.on_click = on_click
        self.idle_color = color
        self.hover_color = hover_color if hover_color is not None else color
        self.pressed_color = pressed_color if pressed_color is not None else color
        self._pressed = False
        self._label = Text(
            state.FRect(0, 0, 1, 1),
            state.Rect(0, 0, 0, 0),
            text=text,
            color=text_color,
            align="center",
            z=1,
        )
        self._label.parent = self
        self._font_comp = Font(font_path=font_path, font_size=font_size)
        self._label.set_component(self._font_comp)

    @property
    def label(self):
        return self._label

    @property
    def text(self):
        return self._label.text

    @text.setter
    def text(self, value: str):
        self._label.text = value

    @property
    def text_color(self):
        return self._label.color

    @text_color.setter
    def text_color(self, value: state.ColorValue):
        self._label.color = value

    @property
    def font_path(self):
        return self._font_comp.font_path

    @font_path.setter
    def font_path(self, value: str | None):
        self._font_comp.font_path = value

    @property
    def font_size(self):
        return self._font_comp.font_size

    @font_size.setter
    def font_size(self, value: int):
        self._font_comp.font_size = value

    def draw(self, workspace: workspace.Workspace, current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler:
        self.color = self.idle_color
        if workspace.is_mouse_over(self):
            self.color = self.hover_color
        if self._pressed:
            self.color = self.pressed_color
        return super().draw(workspace, current_surface)

    def handle_input(self, workspace: workspace.Workspace):
        if self._covering_children_dirty:
            self._update_covering_children()
        can_be_pressed = self._hovered_and_no_covering(workspace)
        if can_be_pressed and workspace.input_state.mousebutton_down(state.MouseButton.LEFT):
            self._pressed = True
        if self._pressed and workspace.input_state.mousebutton_up(state.MouseButton.LEFT):
            self._pressed = False
            if can_be_pressed and self.on_click is not None:
                return self.on_click(workspace)


class Textbox(Panel):
    def __init__(
        self,
        scale: state.FRectValue,
        offset: state.RectValue,
        text: str = "",
        placeholder: str = "",
        color: state.ColorValue = (255, 255, 255),
        font_path: str | None = None,
        font_size: int = 24,
        text_color: state.ColorValue = (0, 0, 0),
        placeholder_color: state.ColorValue = (120, 120, 120),
        align: TextAlign = "topleft",
        max_length: int | None = None,
        is_char_accepted: Callable[[str], bool] | None = None,
        on_text_updated: Callable[[workspace.Workspace], Generator[None, None, None] | None] | None = None,
        confirm_on_click_off: bool = True,
        visible: bool = True,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = False,
        max_scroll_scale: float | None = None,
        max_scroll_offset: int = 0
    ):
        super().__init__(scale, offset, color, visible, enabled, z, ignores_environment, max_scroll_scale, max_scroll_offset)
        self.pre_focus_text = text
        self.text = text
        self.placeholder = placeholder
        self.text_color = text_color
        self.placeholder_color = placeholder_color
        self._value_label = Text(state.FRect(0, 0, 1, 1), state.Rect(0, 0, 0, 0), "", self.placeholder_color, align, enabled=False)
        self._value_label.parent = self
        self._font_comp = Font(font_path=font_path, font_size=font_size)
        self._value_label.set_component(self._font_comp)
        self._caret = Line(
            state.FRect(0, 0, 0, 0),
            state.Rect(0, 0, 0, 0),
            self.text_color,
            width=2,
            enabled=False,
            visible=False,
            z=2,
        )
        self._caret.parent = self
        self.max_length = max_length
        self.is_char_accepted = is_char_accepted
        self.on_text_updated = on_text_updated
        self.confirm_on_click_off = confirm_on_click_off
        self.focused = False
        self._caret_visible = True
        self._caret_timer = 0.0

    @property
    def value_label(self):
        return self._value_label
    
    @property
    def font_path(self):
        return self._font_comp.font_path
    
    @font_path.setter
    def font_path(self, value: str | None):
        self._font_comp.font_path = value

    @property
    def font_size(self):
        return self._font_comp.font_size

    @font_size.setter
    def font_size(self, value: int):
        self._font_comp.font_size = value

    @property
    def caret(self):
        return self._caret

    def draw(self, workspace: workspace.Workspace, current_surface: state.SurfaceHandler | None) -> state.SurfaceHandler:
        display_text = self.text if self.text else self.placeholder
        color = self.text_color if self.text else self.placeholder_color
        self._value_label.text = display_text
        self._value_label.color = color

        if self.focused:
            self._caret_timer += workspace.input_state.dt
            if self._caret_timer > 0.5:
                self._caret_timer = 0.0
                self._caret_visible = not self._caret_visible

            self._caret.visible = self._caret_visible
        else:
            self._caret.visible = False

        if self.focused and self._caret_visible:
            text_specs = self._value_label._get_lines(workspace)

            if len(text_specs) == 0 or self.text.strip() == "":
                caret_x, caret_y = self._value_label._get_base_text_pos(workspace, len(text_specs))
            else:
                last_text_rect = text_specs[-1][1]
                caret_x, caret_y = last_text_rect.topright

            font = self._value_label._get_font()[0]
            caret_h = font.get_ascent()

            textbox_rect = workspace.get_element_rect(self)

            self._caret.offset = state.Rect(
                caret_x - textbox_rect.x,
                caret_y - textbox_rect.y,
                0,
                caret_h,
            )
            self._caret.scale = state.FRect(0, 0, 0, 0)
            self._caret.color = self.text_color
            self._caret.visible = True
        return super().draw(workspace, current_surface)

    def unfocus_revert(self):
        self.focused = False
        self.text = self.pre_focus_text

    def unfocus_confirm(self, workspace: workspace.Workspace):
        self.focused = False

        result = None
        if self.on_text_updated is not None:
            result = self.on_text_updated(workspace)

        self.pre_focus_text = self.text
        return result

    def handle_input(self, workspace: workspace.Workspace):
        super().handle_input(workspace)
        if workspace.input_state.mousebutton_down(state.MouseButton.LEFT):
            if self._hovered_and_no_covering(workspace):
                self.focused = True
            elif self.focused:
                self.focused = False
                if self.confirm_on_click_off:
                    return self.unfocus_confirm(workspace)
                else:
                    return self.unfocus_revert()

        if not self.focused:
            return

        result = None
        if workspace.input_state.key_down(state.Key.BACKSPACE):
            self.text = self.text[:-1]
        elif workspace.input_state.key_down(state.Key.DELETE):
            self.text = ""
        elif workspace.input_state.key_down(state.Key.RETURN):
            result = self.unfocus_confirm(workspace)
        elif workspace.input_state.key_down(state.Key.ESCAPE):
            self.unfocus_revert()

        for chunk in workspace.input_state.text_input:
            if not chunk:
                continue
            if any(ord(ch) < 32 for ch in chunk):
                continue
            if self.is_char_accepted is not None and not self.is_char_accepted(chunk):
                continue
            if self.max_length is not None and len(self.text) >= self.max_length:
                break
            self.text += chunk

        return result


class Tooltip(Panel):
    def __init__(
        self,
        scale: state.FRectValue,
        offset: state.RectValue,
        color: state.ColorValue,
        enabled: bool = True,
        z: int = 0,
        ignores_environment: bool = True,
        max_scroll_scale: float | None = None,
        max_scroll_offset: int = 0,
    ):
        super().__init__(scale, offset, color, False, enabled, z, ignores_environment, max_scroll_scale, max_scroll_offset)

    def handle_input(self, workspace: elements.Workspace):
        self.visible = (
            isinstance(self.parent, Panel) and self.parent._hovered_and_no_covering(workspace)
            or isinstance(self.parent, elements.Element) and workspace.is_mouse_top(self.parent)
            or self.visible and self._hovered_and_no_covering(workspace)
        )
        self.enabled = self.visible
        if self.visible:
            super().handle_input(workspace)
