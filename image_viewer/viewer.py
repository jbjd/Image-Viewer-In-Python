import os
from collections.abc import Callable
from time import perf_counter
from tkinter import Event, Tk
from typing import NoReturn

from PIL.Image import Image
from PIL.ImageTk import PhotoImage

from config import font, max_items_in_cache
from constants import Key, Rotation, TkTags, ZoomDirection
from factories.icon_factory import IconFactory
from helpers.image_loader import ImageLoader
from helpers.image_resizer import ImageResizer
from managers.file_manager import ImageFileManager
from ui.button import HoverableButton, ToggleButton
from ui.canvas import CustomCanvas
from ui.image import DropdownImage
from ui.rename_entry import RenameEntry
from util.image import ImageCache
from util.PIL import create_dropdown_image, image_is_animated, init_PIL


class ViewerApp:
    """Main UI class handling IO and on screen widgets"""

    __slots__ = (
        "_display_image",
        "animation_id",
        "app",
        "canvas",
        "dropdown",
        "file_manager",
        "height_ratio",
        "image_loader",
        "image_load_id",
        "move_id",
        "need_to_redraw",
        "rename_button_id",
        "rename_entry",
        "width_ratio",
    )

    def __init__(self, first_image_path: str, path_to_exe: str) -> None:
        # make FileManager first since it will validate path
        image_cache: ImageCache = ImageCache(max_items_in_cache)
        try:
            self.file_manager: ImageFileManager = ImageFileManager(
                first_image_path, image_cache
            )
        except ValueError:
            self.exit()

        self.need_to_redraw: bool = False
        self.move_id: str = ""
        self.image_load_id: str = ""
        self.animation_id: str = ""

        self.app: Tk = self._setup_tk_app(path_to_exe)
        self.canvas: CustomCanvas = CustomCanvas(self.app)
        screen_height: int = self.canvas.screen_height
        screen_width: int = self.canvas.screen_width

        self.height_ratio: float = screen_height / 1080
        self.width_ratio: float = screen_width / 1920

        self._load_assests(
            self.app,
            self.canvas,
            self.canvas.screen_width,
            self._scale_pixels_to_height(32),
        )

        image_resizer: ImageResizer = ImageResizer(
            screen_width, screen_height, path_to_exe
        )
        self.image_loader: ImageLoader = ImageLoader(
            image_resizer, image_cache, self.animation_loop
        )

        init_PIL(self._scale_pixels_to_height(23))

        self._init_image_display()

        self.canvas.tag_bind(TkTags.BACKGROUND, "<Button-1>", self.handle_canvas_click)
        self._add_keybinds_to_tk()

        self.app.mainloop()

    @staticmethod
    def _setup_tk_app(path_to_exe: str) -> Tk:
        """Creates and setups Tk class"""
        app: Tk = Tk()
        app.attributes("-fullscreen", True)

        if os.name == "nt":
            app.state("zoomed")
            app.wm_iconbitmap(default=os.path.join(path_to_exe, "icon/icon.ico"))
        else:
            from tkinter import PhotoImage as tkPhotoImage

            app.wm_iconphoto(
                True, tkPhotoImage(file=os.path.join(path_to_exe, "icon/icon.png"))
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

    def _add_keybinds_to_tk(self) -> None:
        """Assigns keybinds to app"""
        app: Tk = self.app
        app.bind("<FocusIn>", self.redraw)
        app.bind("<Escape>", self.handle_esc)
        app.bind("<KeyPress>", self.handle_key)
        app.bind("<KeyRelease>", self.handle_key_release)
        app.bind("<Control-r>", self.refresh)
        app.bind(
            "<Control-d>",
            lambda _: self.file_manager.show_image_detail_popup(
                self.image_loader.PIL_image
            ),
        )
        app.bind("<Control-m>", self.move_to_new_file)
        app.bind("<Control-z>", self.undo_rename_or_convert)
        app.bind("<F2>", self.toggle_show_rename_window)
        app.bind("<F5>", lambda _: self.load_image_unblocking())
        app.bind("<Up>", self.hide_topbar)
        app.bind("<Down>", self.show_topbar)
        app.bind("<Alt-Left>", self.handle_rotate_image)
        app.bind("<Alt-Right>", self.handle_rotate_image)
        app.bind("<Alt-Up>", self.handle_rotate_image)
        app.bind("<Alt-Down>", self.handle_rotate_image)

        if os.name == "nt":
            app.bind(
                "<MouseWheel>",
                lambda event: self.handle_mouse_wheel(event),
            )
        else:
            app.bind("<Button-4>", lambda event: self.handle_mouse_wheel(event))
            app.bind("<Button-5>", lambda event: self.handle_mouse_wheel(event))

    def _load_assests(  # TODO: port this into canvas.py?
        self, app: Tk, canvas: CustomCanvas, screen_width: int, topbar_height: int
    ) -> None:
        """Load all assets on topbar and create canvas items"""

        icon_size: int = topbar_height + (topbar_height % 2)  # ensure even number

        font_family: str = font[:-4].lower()  # -4 chops extension .ttf/.otf
        # negative size makes font absolute for consistency with different monitors
        FONT: str = f"{font_family} -{self._scale_pixels_to_height(18)}"

        icon_factory: IconFactory = IconFactory(icon_size)

        canvas.create_topbar(icon_factory.make_topbar_image(screen_width))
        # weird case, scale x offset by height, not width, since icon to its left
        # is scaled by height, small screen could overlap otherwise
        canvas.create_name_text(
            self._scale_pixels_to_height(36), self._scale_pixels_to_height(16), FONT
        )

        button_x_offset: int = screen_width - icon_size
        exit_button: HoverableButton = HoverableButton(
            canvas,
            icon_factory.make_exit_icons(),
            self.exit,
        )
        exit_button.add_to_canvas(button_x_offset)

        button_x_offset -= icon_size
        minify_button: HoverableButton = HoverableButton(
            canvas, icon_factory.make_minify_icons(), self.minimize
        )
        minify_button.add_to_canvas(button_x_offset)

        button_x_offset -= icon_size
        dropdown_button: ToggleButton = ToggleButton(
            canvas, *icon_factory.make_dropdown_icons(), self.handle_dropdown
        )
        dropdown_button.add_to_canvas(button_x_offset)

        trash_button: HoverableButton = HoverableButton(
            canvas, icon_factory.make_trash_icons(), self.trash_image
        )
        trash_button.add_to_canvas()

        rename_button: HoverableButton = HoverableButton(
            canvas, icon_factory.make_rename_icons(), self.toggle_show_rename_window
        )
        rename_button.add_to_canvas()
        self.rename_button_id: int = rename_button.id

        dropdown_id: int = canvas.create_image(
            screen_width, icon_size, anchor="ne", tag=TkTags.TOPBAR, state="hidden"
        )
        self.dropdown: DropdownImage = DropdownImage(dropdown_id)

        rename_window_width: int = self._scale_pixels_to_width(250)
        rename_id: int = canvas.create_window(
            0,
            0,
            width=rename_window_width,
            height=int(icon_size * 0.8),
            anchor="nw",
        )
        self.rename_entry: RenameEntry = RenameEntry(
            app, canvas, rename_id, rename_window_width, font=FONT
        )
        self.rename_entry.bind("<Return>", self.rename_or_convert)

    def _scale_pixels_to_height(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.height_ratio)

    def _scale_pixels_to_width(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.width_ratio)

    # Functions handling specific user input

    def handle_mouse_wheel(self, event: Event) -> None:
        """On mouse wheel, either moves between images
        or zooms when right mouse also held"""
        right_mouse_held: bool = event.state & 1024  # type: ignore

        if right_mouse_held:
            self.load_zoomed_image_unblocking(
                ZoomDirection.IN if event.delta > 0 else ZoomDirection.OUT
            )
        else:
            self.move(-1 if event.delta > 0 else 1)

    def handle_rotate_image(self, event: Event) -> None:
        """Rotates image, saves it to disk, and updates the display"""
        if self._currently_animating():
            return

        match event.keycode:
            case Key.LEFT:
                angle = Rotation.LEFT
            case Key.RIGHT:
                angle = Rotation.RIGHT
            case _:
                angle = Rotation.FLIP

        self.image_loader.reset_and_setup()

        path: str = self.file_manager.path_to_image
        image: Image | None = self.image_loader.get_PIL_image(path)
        if image is None:
            return

        with image:
            if image_is_animated(image):
                return
            try:
                self.file_manager.rotate_image_and_save(image, angle)
                self.load_image_unblocking()
            except (FileNotFoundError, OSError):
                pass

    def handle_canvas_click(self, _: Event) -> None:
        """Toggles the display of topbar when non-topbar area clicked"""
        if self.canvas.is_widget_visible(TkTags.TOPBAR):
            self.hide_topbar()
        else:
            self.show_topbar()

    def handle_key(self, event: Event) -> None:
        """Key binds that happen only on main app focus"""
        if event.widget is self.app:
            match event.keycode:
                case Key.LEFT | Key.RIGHT:
                    self.handle_lr_arrow(event)
                case Key.EQUALS:
                    self.load_zoomed_image_unblocking(ZoomDirection.IN)
                case Key.MINUS:
                    self.load_zoomed_image_unblocking(ZoomDirection.OUT)
                case Key.R:
                    self.toggle_show_rename_window(event)

    def handle_key_release(self, event: Event) -> None:
        """Handle key release, current just used for L/R arrow release"""
        if self.move_id != "" and event.keycode in (Key.LEFT, Key.RIGHT):
            self.app.after_cancel(self.move_id)
            self.move_id = ""

    def handle_lr_arrow(self, event: Event) -> None:
        """Handle L/R arrow key input
        Doesn't move when main window unfocused"""
        if self.move_id == "":
            # move +4 when ctrl held, +1 when shift held
            move_amount: int = 1 + (event.state & 5)  # type: ignore
            if event.keycode == Key.LEFT:
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

    def handle_dropdown(self, _: Event) -> None:
        """Handle when user clicks on the dropdown arrow"""
        self.dropdown.toggle_display()
        self.update_details_dropdown()

    def load_zoomed_image(self, direction: ZoomDirection) -> None:
        """Loads zoomed image and updates display"""
        zoomed_image: Image | None = self.image_loader.get_zoomed_image(direction)
        if zoomed_image is not None:
            self._update_existing_image_display(zoomed_image)

        self._end_image_load()

    def load_zoomed_image_unblocking(self, direction: ZoomDirection) -> None:
        """Starts new thread for loading zoomed image"""
        if self._currently_animating():
            return

        self._start_image_load(self.load_zoomed_image, direction)

    # End functions handling specific user input

    def move_to_new_file(self, _: Event) -> None:
        """Moves to a new image from file dialog"""
        moved: bool = self.file_manager.move_to_new_directory()
        if moved:
            self.load_image()

    def exit(self, _: Event | None = None, exit_code: int = 0) -> NoReturn:
        """Safely exits the program"""
        # This prevents an ignored exception since Tk may clean up
        # before PIL does. Lets leave the work to Tk when exiting
        del PhotoImage.__del__

        try:
            self.canvas.delete(self.canvas.file_name_text_id)
            self.app.quit()
            self.app.destroy()
            self.image_loader.reset_and_setup()
        except AttributeError:
            pass

        raise SystemExit(exit_code)  # exit(0) here didn't work with --standalone

    def minimize(self, _: Event) -> None:
        """Minimizes the app and sets flag to redraw current image when opened again"""
        self.need_to_redraw = True
        self.app.iconify()
        if self.move_id != "":
            self.app.after_cancel(self.move_id)

    def refresh(self, _: Event) -> None:
        """Gets images in current directory and update internal list with them"""
        self.clear_image()
        try:
            self.file_manager.refresh_image_list()
        except IndexError:
            self.exit()
        self.load_image_unblocking()

    def undo_rename_or_convert(self, _: Event) -> None:
        if self.file_manager.undo_rename_or_convert():
            self.load_image_unblocking()

    def move(self, amount: int) -> None:
        """Moves to different image
        amount: any non-zero value indicating movement to next or previous"""
        self.hide_rename_window()
        self.file_manager.move_index(amount)
        self.load_image_unblocking()

    def redraw(self, event: Event) -> None:
        """Redraws screen if current image has a different size than when it was loaded,
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
        self.canvas.itemconfigure(self.rename_entry.id, state="hidden")
        self.app.focus()

    def toggle_show_rename_window(self, _: Event) -> None:
        if self.canvas.is_widget_visible(self.rename_entry.id):
            self.hide_rename_window()
            return

        if not self.canvas.is_widget_visible(TkTags.TOPBAR):
            self.show_topbar()

        self.canvas.itemconfigure(self.rename_entry.id, state="normal")
        self.rename_entry.focus()

    def rename_or_convert(self, _: Event) -> None:
        """Handles user input into rename window.
        Tries to convert or rename based on input"""
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
        Call this when the new image is the same or a variant of the displaying image"""
        self._display_image = PhotoImage(image)
        self.canvas.update_existing_image_display(self._display_image)

    def _update_image_display(self, image: Image) -> None:
        """Updates display with PhotoImage version of provided Image.
        This will re-center the image and create a new display"""
        self._display_image = PhotoImage(image)
        self.canvas.update_image_display(self._display_image)

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
        """Hides/removes focus from all topbar elements"""
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
        self.canvas.coords(self.rename_button_id, rename_window_x_offset, 0)
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
        frame: Image | None
        ms_until_next_frame: int
        frame, ms_until_next_frame = self.image_loader.get_next_frame()

        if frame is None:  # trying to display frame before it is loaded
            ms_until_next_frame = ms_backoff = int(ms_backoff * 1.4)
        else:
            self._update_existing_image_display(frame)
            elapsed: int = round((perf_counter() - start) * 1000)
            ms_until_next_frame = max(ms_until_next_frame - elapsed, 1)

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
        if dropdown.showing:
            if dropdown.need_refresh:
                try:
                    details: str = self.file_manager.get_cached_details()
                except KeyError:
                    return  # data not present in cache

                # remove last line since I don't want to show mode in this dropdown
                details = details[: details.rfind("\n", 0, -9) - 1]
                dropdown.image = create_dropdown_image(details)

            self.canvas.itemconfigure(dropdown.id, image=dropdown.image, state="normal")
        else:
            self.canvas.itemconfigure(dropdown.id, state="hidden")

    def _start_image_load(self, function: Callable, *args):
        """Cancels any previous image load thread and starts a new one"""
        if self.image_load_id != "":
            self.app.after_cancel(self.image_load_id)

        self.image_load_id = self.app.after(0, function, *args)

    def _end_image_load(self) -> None:
        """Indicates function called by _start_image_load has finished"""
        self.image_load_id = ""
