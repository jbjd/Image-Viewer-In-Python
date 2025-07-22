import os
from collections.abc import Callable
from time import perf_counter
from tkinter import Event, Tk
from typing import NoReturn

from PIL.Image import Image
from PIL.ImageTk import PhotoImage

from animation.frame import Frame
from config import Config
from constants import ButtonName, Key, Rotation, TkTags, ZoomDirection
from files.file_manager import ImageFileManager
from image.cache import ImageCache
from image.loader import ImageLoader
from ui.button import HoverableButtonUIElement, ToggleableButtonUIElement
from ui.button_icon_factory import ButtonIconFactory
from ui.canvas import CustomCanvas
from ui.image import DropdownImageUIElement
from ui.rename_entry import RenameEntry
from util.io import read_file_as_base64
from util.os import show_info_popup
from util.PIL import create_dropdown_image, init_PIL


class ViewerApp:
    """Main UI class handling IO and on screen widgets"""

    __slots__ = (
        "animation_id",
        "app",
        "app_id",
        "canvas",
        "dropdown",
        "file_manager",
        "height_ratio",
        "image_loader",
        "image_load_id",
        "move_id",
        "need_to_redraw",
        "rename_entry",
        "width_ratio",
    )

    def __init__(self, first_image_path: str, path_to_exe_folder: str) -> None:
        config = Config(path_to_exe_folder)
        image_cache: ImageCache = ImageCache(config.max_items_in_cache)
        self.file_manager: ImageFileManager = ImageFileManager(
            first_image_path, image_cache
        )
        try:
            self.file_manager.validate_current_path()
        except ValueError:
            self.exit()

        self.need_to_redraw: bool = False
        self.move_id: str = ""
        self.image_load_id: str = ""
        self.animation_id: str = ""

        self.app: Tk = self._setup_tk_app(path_to_exe_folder)
        self.app_id: int = self.app.winfo_id()
        self.canvas: CustomCanvas = CustomCanvas(self.app, config.background_color)
        screen_height: int = self.canvas.screen_height
        screen_width: int = self.canvas.screen_width

        self.height_ratio: float = screen_height / 1080
        self.width_ratio: float = screen_width / 1920

        self._load_assets(
            self.canvas,
            config.font_file,
            self.canvas.screen_width,
            self._scale_pixels_to_height(32),
        )

        self.image_loader: ImageLoader = ImageLoader(
            path_to_exe_folder,
            screen_width,
            screen_height,
            image_cache,
            self.animation_loop,
        )

        init_PIL(config.font_file, self._scale_pixels_to_height(23))

        self._init_image_display()

        self.canvas.tag_bind(TkTags.BACKGROUND, "<Button-1>", self.handle_canvas_click)
        self._add_binds_to_tk(config)

        self.app.mainloop()

    @staticmethod
    def _setup_tk_app(path_to_exe_folder: str) -> Tk:
        """Creates and setups Tk class"""
        app: Tk = Tk()
        app.attributes("-fullscreen", True)

        if os.name == "nt":
            app.state("zoomed")
            app.wm_iconbitmap(default=os.path.join(path_to_exe_folder, "icon/icon.ico"))
        else:
            from tkinter import PhotoImage as tkPhotoImage

            app.wm_iconphoto(
                True,
                tkPhotoImage(file=os.path.join(path_to_exe_folder, "icon/icon.png")),
            )
            del tkPhotoImage

        return app

    def _init_image_display(self) -> None:
        """Loads first image and then finds all images files in the directory"""
        # Don't call this class's load_image here since we only consider there
        # to be one image now, and that function would throw if that one failed to load
        image: Image | None = self._load_image_at_current_path()

        if image is not None:
            self.update_after_image_load(image)

        self.file_manager.find_all_images()

        # if first load failed, load new one now that all other images are found
        if image is None:
            self.load_image()

    def _add_binds_to_tk(self, config: Config) -> None:
        """Assigns binds to Tk instance"""
        app: Tk = self.app
        app.bind("<FocusIn>", self.redraw)
        app.bind("<Escape>", self.handle_esc)
        app.bind("<KeyPress>", self.handle_key)
        app.bind("<KeyRelease>", self.handle_key_release)
        app.bind("<Control-r>", self.refresh)
        app.bind("<Control-E>", self.copy_file_to_clipboard_as_base64)
        app.bind(config.keybinds.show_details, self.show_details_popup)
        app.bind(config.keybinds.move_to_new_file, self.move_to_new_file)
        app.bind(config.keybinds.undo_most_recent_action, self.undo_most_recent_action)
        app.bind("<F2>", self.toggle_show_rename_window)
        app.bind(
            "<r>",
            lambda e: self._only_for_this_window(e, self.toggle_show_rename_window),
        )
        app.bind("<F5>", lambda _: self.load_image_unblocking())
        app.bind("<Up>", self.handle_up_arrow)
        app.bind("<Down>", self.handle_down_arrow)
        app.bind("<Alt-Left>", self.handle_rotate_image)
        app.bind("<Alt-Right>", self.handle_rotate_image)
        app.bind("<Alt-Up>", self.handle_rotate_image)
        app.bind("<Alt-Down>", self.handle_rotate_image)

        if os.name == "nt":
            from util._os import drop_file_to_clipboard, open_with

            app.bind(
                "<Control-b>",
                lambda _: open_with(self.app_id, self.file_manager.path_to_image),
            )
            app.bind(
                "<Control-D>",
                lambda _: drop_file_to_clipboard(
                    self.app_id, self.file_manager.path_to_image
                ),
            )
            app.bind(
                "<MouseWheel>",
                lambda event: self.handle_mouse_wheel(event),
            )
        else:
            app.bind("<Button-4>", lambda event: self.handle_mouse_wheel(event))
            app.bind("<Button-5>", lambda event: self.handle_mouse_wheel(event))

    def _load_assets(
        self,
        canvas: CustomCanvas,
        font_file: str,
        screen_width: int,
        topbar_height: int,
    ) -> None:
        """Load all assets on topbar and create canvas items"""

        icon_size: int = topbar_height + (topbar_height % 2)  # ensure even number

        font_family: str = font_file[:-4].lower()  # -4 chops extension .ttf/.otf
        # negative size makes font absolute for consistency with different monitors
        FONT: str = f"{font_family} -{self._scale_pixels_to_height(18)}"

        button_icon_factory = ButtonIconFactory(icon_size)

        canvas.create_topbar(button_icon_factory.make_topbar_image(screen_width))
        # weird case, scale x offset by height, not width, since icon to its left
        # is scaled by height, small screen could overlap otherwise
        canvas.create_name_text(
            self._scale_pixels_to_height(36), self._scale_pixels_to_height(16), FONT
        )

        button_x_offset: int = screen_width - icon_size
        exit_button = HoverableButtonUIElement(
            canvas,
            button_icon_factory.make_exit_icons(),
            self.exit,
        )
        exit_button.add_to_canvas(ButtonName.EXIT, button_x_offset)

        button_x_offset -= icon_size
        minify_button = HoverableButtonUIElement(
            canvas, button_icon_factory.make_minify_icons(), self.minimize
        )
        minify_button.add_to_canvas(ButtonName.MINIFY, button_x_offset)

        button_x_offset -= icon_size
        dropdown_button = ToggleableButtonUIElement(
            canvas, *button_icon_factory.make_dropdown_icons(), self.handle_dropdown
        )
        dropdown_button.add_to_canvas(ButtonName.DROPDOWN, button_x_offset)

        trash_button = HoverableButtonUIElement(
            canvas, button_icon_factory.make_trash_icons(), self.trash_image
        )
        trash_button.add_to_canvas(ButtonName.TRASH)

        rename_button = HoverableButtonUIElement(
            canvas,
            button_icon_factory.make_rename_icons(),
            self.toggle_show_rename_window,
        )
        rename_button.add_to_canvas(ButtonName.RENAME)

        dropdown_id: int = canvas.create_image(
            screen_width, icon_size, anchor="ne", tag=TkTags.TOPBAR, state="hidden"
        )
        self.dropdown = DropdownImageUIElement(dropdown_id)

        rename_window_width: int = self._scale_pixels_to_width(250)
        rename_id: int = canvas.create_window(
            0,
            0,
            width=rename_window_width,
            height=int(icon_size * 0.8),
            anchor="nw",
        )
        self.rename_entry: RenameEntry = RenameEntry(
            self.app, canvas, rename_id, rename_window_width, font=FONT
        )
        self.rename_entry.bind("<Return>", self.rename_or_convert)

    def _scale_pixels_to_height(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.height_ratio)

    def _scale_pixels_to_width(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1920 pixel wide screen"""
        return int(original_pixels * self.width_ratio)

    # Functions handling specific user input

    def handle_mouse_wheel(self, event: Event) -> None:
        """On mouse wheel: either moves between images
        or zooms when right mouse held"""
        right_mouse_held: bool = getattr(event, "state", 0) & 1024 == 1024

        if right_mouse_held:
            self.load_zoomed_or_rotated_image_unblocking(
                ZoomDirection.IN if event.delta > 0 else ZoomDirection.OUT
            )
        else:
            self.move(-1 if event.delta > 0 else 1)

    def handle_rotate_image(self, event: Event) -> None:
        """Rotates image, saves it to disk, and updates the display"""
        if self._currently_animating():
            return

        match event.keysym_num:
            case Key.LEFT:
                rotation = Rotation.LEFT
            case Key.RIGHT:
                rotation = Rotation.RIGHT
            case Key.DOWN:
                rotation = Rotation.DOWN
            case _:
                rotation = Rotation.UP

        self.load_zoomed_or_rotated_image_unblocking(rotation=rotation)

    def handle_canvas_click(self, _: Event) -> None:
        """Toggles the display of topbar when non-topbar area clicked"""
        if self.canvas.is_widget_visible(TkTags.TOPBAR):
            self.hide_topbar()
        else:
            self.show_topbar()

    def _only_for_this_window(
        self, event: Event, callable: Callable[[Event | None], None]
    ) -> None:
        """Given a callable that accepts a tkinter Event,
        only call it if self.app is the target"""
        if event.widget is self.app:
            callable(event)

    def handle_key(self, event: Event) -> None:
        """Key binds that happen only on main app focus"""
        if event.widget is self.app:
            match event.keysym_num:
                case Key.LEFT | Key.RIGHT:
                    self.handle_lr_arrow(event)
                case Key.EQUALS:
                    self.load_zoomed_or_rotated_image_unblocking(ZoomDirection.IN)
                case Key.MINUS:
                    self.load_zoomed_or_rotated_image_unblocking(ZoomDirection.OUT)

    def handle_key_release(self, event: Event) -> None:
        """Handle key release, current just used for L/R arrow release"""
        if self.move_id != "" and event.keysym_num in (Key.LEFT, Key.RIGHT):
            self.app.after_cancel(self.move_id)
            self.move_id = ""

    def handle_lr_arrow(self, event: Event) -> None:
        """Handle L/R arrow key input
        Doesn't move when main window unfocused"""
        if self.move_id == "":
            # move +4 when ctrl held, +1 when shift held
            move_amount: int = 1 + (getattr(event, "state", 0) & 5)
            if event.keysym_num == Key.LEFT:
                move_amount = -move_amount
            self.move(move_amount)
            self._repeat_move(move_amount, 500)

    def _repeat_move(self, move_amount: int, ms: int) -> None:
        """Repeat move to next image while L/R key held"""
        if self.move_id != "":
            self.move(move_amount)
            self.move_id = self.app.after(ms, self._repeat_move, move_amount, 200)

    def handle_esc(self, _: Event) -> None:
        """Closes rename window, then program on hitting escape"""
        if self.canvas.is_widget_visible(self.rename_entry.id):
            self.hide_rename_window()
            return
        self.exit()

    def handle_up_arrow(self, _: Event):
        if self.canvas.is_widget_visible(self.dropdown.id):
            self.canvas.mock_button_click(ButtonName.DROPDOWN)
        else:
            self.hide_topbar()

    def handle_down_arrow(self, _: Event):
        if self.canvas.is_widget_visible(TkTags.TOPBAR):
            if not self.canvas.is_widget_visible(self.dropdown.id):
                self.canvas.mock_button_click(ButtonName.DROPDOWN)
        else:
            self.show_topbar()

    def handle_dropdown(self, _: Event | None = None) -> None:
        """Handle when user clicks on the dropdown arrow"""
        self.dropdown.toggle_display()
        self.update_details_dropdown()

    def copy_file_to_clipboard_as_base64(self, _: Event) -> None:
        """Converts the file's bytes into base64 and copies
        it to the clipboard"""

        try:
            image_base64: str = read_file_as_base64(self.file_manager.path_to_image)
            self._copy_to_clipboard(image_base64)
        except (FileNotFoundError, OSError):
            pass

    def show_details_popup(self, _: Event | None = None) -> None:
        """Gets details on image and shows it in a UI popup"""
        details: str | None = self.file_manager.get_image_details(
            self.image_loader.PIL_image
        )

        if details is not None:
            show_info_popup(self.app_id, "Image Details", details)

    def load_zoomed_or_rotated_image(
        self, direction: ZoomDirection | None, rotation: Rotation | None
    ) -> None:
        """Loads zoomed image and updates display"""
        if direction is None and rotation is None:
            raise ValueError

        zoomed_image: Image | None = self.image_loader.get_zoomed_or_rotated_image(
            direction, rotation
        )
        if zoomed_image is not None:
            self._update_existing_image_display(zoomed_image)

        self._end_image_load()

    def load_zoomed_or_rotated_image_unblocking(
        self, direction: ZoomDirection | None = None, rotation: Rotation | None = None
    ) -> None:
        """Starts new thread for loading zoomed image"""
        if self._currently_animating():
            return

        self._start_image_load(self.load_zoomed_or_rotated_image, direction, rotation)

    # End functions handling specific user input

    def move_to_new_file(self, _: Event) -> None:
        """Moves to a new image from file dialog"""
        if self.file_manager.move_to_new_file():
            self.load_image()

    def exit(self, _: Event | None = None, exit_code: int = 0) -> NoReturn:
        """Safely exits the program"""
        try:
            self.canvas.delete(self.canvas.file_name_text_id)
            self.app.quit()
            self.app.destroy()
            self.image_loader.reset_and_setup()
        except AttributeError:
            pass

        raise SystemExit(exit_code)  # exit(0) here didn't work with --standalone

    def minimize(self, _: Event | None = None) -> None:
        """Minimizes the app and sets flag to redraw current image when opened again"""
        self.need_to_redraw = True
        self.app.iconify()
        if self.move_id != "":
            self.app.after_cancel(self.move_id)

    def refresh(self, _: Event) -> None:
        """Updates list of all images in directory.
        Display may change if image was removed outside of program"""
        self.clear_image()
        try:
            self.file_manager.refresh_image_list()
        except IndexError:
            self.exit()
        self.load_image_unblocking()

    def undo_most_recent_action(self, _: Event) -> None:
        """Tries to undo most recent action and loads new image if needed"""
        if self.file_manager.undo_most_recent_action():
            self.load_image_unblocking()

    def move(self, amount: int) -> None:
        """Moves some amount of images forward/backward"""
        self.hide_rename_window()
        self.file_manager.move_index(amount)
        self.load_image_unblocking()

    def redraw(self, event: Event) -> None:
        """Redraws screen if current image has a different size then when it was loaded,
        implying it was edited outside of the program"""
        if event.widget is not self.app or not self.need_to_redraw:
            return
        self.need_to_redraw = False
        if self.file_manager.current_image_cache_still_fresh():
            return
        self.load_image_unblocking()

    def trash_image(self, _: Event | None = None) -> None:
        """Move current image to trash and moves to next"""
        self.clear_image()
        self.hide_rename_window()
        self.delete_current_image()
        self.load_image_unblocking()

    def hide_rename_window(self) -> None:
        """Hides rename window and returns focus to main window"""
        self.canvas.itemconfigure(self.rename_entry.id, state="hidden")
        self.app.focus()

    def show_rename_window(self) -> None:
        """Shows rename window and moves focus to it"""
        if not self.canvas.is_widget_visible(TkTags.TOPBAR):
            self.show_topbar()

        self.canvas.itemconfigure(self.rename_entry.id, state="normal")
        self.rename_entry.focus()

    def toggle_show_rename_window(self, _: Event | None = None) -> None:
        """Either shows or hides rename window and shifts focus accordingly"""
        if self.canvas.is_widget_visible(self.rename_entry.id):
            self.hide_rename_window()
        else:
            self.show_rename_window()

    def rename_or_convert(self, _: Event) -> None:
        """Tries to rename or convert current image based on input.
        Makes window flash red if operation failed"""
        user_input: str = self.rename_entry.get()
        if user_input == "":
            return
        try:
            self.file_manager.rename_or_convert_current_image(user_input)
        except (OSError, FileExistsError, ValueError):
            self.rename_entry.error_flash()
            return
        except IndexError:
            self.exit()

        # Cleanup after successful rename
        self.hide_rename_window()
        self.load_image_unblocking()

    def _update_existing_image_display(self, image: Image) -> None:
        """Updates display with PhotoImage version of provided Image.
        Use when the displayed image hasn't changed, but moved or went to a new frame"""
        self.canvas.update_existing_image_display(PhotoImage(image))

    def _update_image_display(self, image: Image) -> None:
        """Updates display with PhotoImage version of provided Image.
        Use when a new image is replacing the previous and should be
        re-centered"""
        self.canvas.update_image_display(PhotoImage(image))

    def update_after_image_load(self, image: Image) -> None:
        """Updates app title and displayed image"""
        self._update_image_display(image)
        self.app.title(self.file_manager.current_image.name)

    def _load_image_at_current_path(self) -> Image | None:
        """Wraps ImageLoader's load call with path from FileManager"""
        return self.image_loader.load_image(self.file_manager.path_to_image)

    def load_image(self) -> None:
        """Loads an image and updates display"""
        self.clear_image()

        # When load fails, keep removing bad image and trying to load next
        current_image: Image | None
        while (current_image := self._load_image_at_current_path()) is None:
            self.remove_current_image()

        self.update_after_image_load(current_image)
        if self.canvas.is_widget_visible(TkTags.TOPBAR):
            self.update_topbar()

        self._end_image_load()

    def load_image_unblocking(self) -> None:
        """Starts new thread for loading image"""
        self.dropdown.need_refresh = True
        self._start_image_load(self.load_image)

    def show_topbar(self, _: Event | None = None) -> None:
        """Shows all topbar elements and updates its display"""
        self.canvas.itemconfigure(TkTags.TOPBAR, state="normal")
        self.update_topbar()

    def hide_topbar(self, _: Event | None = None) -> None:
        """Hides and removes focus from all topbar elements"""
        self.canvas.itemconfigure(TkTags.TOPBAR, state="hidden")
        self.hide_rename_window()

    def remove_current_image(self) -> None:
        """Removes current image from internal image list"""
        try:
            self.file_manager.remove_current_image()
        except IndexError:
            self.exit()

    def delete_current_image(self) -> None:
        """Deletes current image from disk list"""
        try:
            self.file_manager.delete_current_image()
        except IndexError:
            self.exit()

    def update_topbar(self) -> None:
        """Updates all elements on the topbar with current info"""
        rename_window_x_offset = self.canvas.update_file_name(
            self.file_manager.current_image.name
        )
        self.canvas.coords(
            self.canvas.get_button_id(ButtonName.RENAME), rename_window_x_offset, 0
        )
        self.canvas.coords(
            self.rename_entry.id,
            rename_window_x_offset + self._scale_pixels_to_height(40),
            self._scale_pixels_to_height(4),
        )

        self.update_details_dropdown()

    def _currently_animating(self) -> bool:
        """Returns True when currently in an animation loop"""
        return self.animation_id != ""

    def animation_loop(self, ms_until_next_frame: int, ms_backoff: int) -> None:
        """Handles looping between animation frames"""
        self.animation_id = self.app.after(
            ms_until_next_frame, self.show_next_frame, ms_backoff
        )

    def show_next_frame(self, ms_backoff: int) -> None:
        """Displays a frame on screen and loops to next frame after a delay"""
        start: float = perf_counter()
        frame: Frame | None = self.image_loader.get_next_frame()

        ms_until_next_frame: int
        if frame is None:  # trying to display frame before it is loaded
            ms_until_next_frame = ms_backoff
            ms_backoff = int(ms_backoff * 1.4)
        else:
            self._update_existing_image_display(frame.image)
            elapsed: int = round((perf_counter() - start) * 1000)
            ms_until_next_frame = max(frame.ms_until_next_frame - elapsed, 1)

        self.animation_loop(ms_until_next_frame, ms_backoff)

    def clear_image(self) -> None:
        """Clears all image data"""
        if self._currently_animating():
            self.app.after_cancel(self.animation_id)
            self.animation_id = ""
        self.image_loader.reset_and_setup()

    def update_details_dropdown(self) -> None:
        """Updates the information and state of dropdown image"""
        dropdown = self.dropdown
        if dropdown.show:
            if dropdown.need_refresh:
                try:
                    details: str = self.file_manager.get_cached_metadata(
                        get_all_details=False
                    )
                except KeyError:
                    return  # data not present in cache

                dropdown.image = PhotoImage(create_dropdown_image(details))

            self.canvas.itemconfigure(dropdown.id, image=dropdown.image, state="normal")
        else:
            self.canvas.itemconfigure(dropdown.id, state="hidden")

    def _copy_to_clipboard(self, text: str) -> None:
        self.app.clipboard_clear()
        self.app.clipboard_append(text)

    def _start_image_load(self, function: Callable, *args):
        """Cancels any previous image load thread and starts a new one"""
        if self.image_load_id != "":
            self.app.after_cancel(self.image_load_id)

        self.image_load_id = self.app.after(0, function, *args)

    def _end_image_load(self) -> None:
        """Indicates function called by _start_image_load has finished"""
        self.image_load_id = ""
