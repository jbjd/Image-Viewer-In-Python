import os
from time import perf_counter
from tkinter import Event, Tk
from typing import Literal, NoReturn

from PIL.ImageTk import PhotoImage

from constants import TOPBAR_TAG, Key
from factories.icon_factory import IconFactory
from helpers.image_loader import ImageLoader
from helpers.image_resizer import ImageResizer
from managers.file_manager import ImageFileManager
from ui.button import HoverableButton, ToggleButton
from ui.canvas import CustomCanvas
from ui.image import DropdownImage
from ui.rename_entry import RenameEntry
from util.image import ImageCache
from util.PIL import create_dropdown_image, init_PIL


class ViewerApp:
    """Main UI class handling IO and on screen widgets"""

    __slots__ = (
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
        image_cache = ImageCache()
        try:
            self.file_manager = ImageFileManager(first_image_path, image_cache)
        except ValueError:
            self.exit(exit_code=1)

        self.need_to_redraw: bool = False
        self.move_id: str = ""
        self.image_load_id: str = ""
        self.animation_id: str = ""

        self.app: Tk = self._setup_tk_app(path_to_exe)
        canvas = CustomCanvas(self.app)
        self.canvas = canvas

        self.height_ratio: float = canvas.screen_height / 1080
        self.width_ratio: float = canvas.screen_width / 1920

        self._load_assests(
            self.app, canvas, canvas.screen_width, self._scale_pixels_to_height(32)
        )

        # set up and draw first image, then get all image paths in directory
        self.image_loader = ImageLoader(
            ImageResizer(canvas.screen_width, canvas.screen_height, path_to_exe),
            image_cache,
            self.animation_loop,
        )

        init_PIL(self._scale_pixels_to_height(23))

        self._init_image_display()

        self.canvas.tag_bind("back", "<Button-1>", self.handle_canvas_click)
        self._add_keybinds_to_tk()

        self.bring_tk_to_front()
        self.app.mainloop()

    @staticmethod
    def _setup_tk_app(path_to_exe: str) -> Tk:
        """Creates and setups Tk class"""
        app = Tk()
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
        current_image: PhotoImage | None = self._load_image_at_current_path()

        if current_image is not None:
            self.update_after_image_load(current_image)

        self.file_manager.find_all_images()

        # if first load failed, load new one now that all images are loaded
        if current_image is None:
            self.load_image()

    def _add_keybinds_to_tk(self) -> None:
        """Assigns keybinds to app"""
        app = self.app
        app.bind("<FocusIn>", self.redraw)
        app.bind("<Escape>", self.handle_esc)
        app.bind("<KeyPress>", self.handle_key)
        app.bind("<KeyRelease>", self.handle_key_release)
        app.bind("<Control-r>", self.refresh)
        app.bind(
            "<Control-d>",
            lambda _: self.file_manager.show_image_details(self.image_loader.PIL_image),
        )
        app.bind("<Control-m>", self.move_to_new_file)
        app.bind("<Control-z>", self.undo_rename_or_convert)
        app.bind("<F2>", self.toggle_show_rename_window)
        app.bind("<F5>", lambda _: self.load_image_unblocking())
        app.bind("<Up>", self.hide_topbar)
        app.bind("<Down>", self.show_topbar)
        app.bind("<Alt-Left>", self.canvas.handle_alt_arrow_keys)
        app.bind("<Alt-Right>", self.canvas.handle_alt_arrow_keys)
        app.bind("<Alt-Up>", self.canvas.handle_alt_arrow_keys)
        app.bind("<Alt-Down>", self.canvas.handle_alt_arrow_keys)

        if os.name == "nt":
            app.bind(
                "<MouseWheel>", lambda event: self.move(-1 if event.delta > 0 else 1)
            )
        else:
            app.bind("<Button-4>", lambda _: self.move(-1))
            app.bind("<Button-5>", lambda _: self.move(1))

    def _load_assests(  # TODO: port this into canvas.py?
        self, app: Tk, canvas: CustomCanvas, screen_width: int, topbar_height: int
    ) -> None:
        """
        Load all assets on topbar from factory and create tkinter objects
        topbar_height: size to make icons/topbar
        """

        icon_size: int = topbar_height + (topbar_height % 2)  # ensure even number

        # negative makes it an absolute size for consistency with different monitors
        FONT: str = f"arial -{self._scale_pixels_to_height(18)}"

        icon_factory = IconFactory(icon_size)

        canvas.create_topbar(icon_factory.make_topbar(screen_width))
        # weird case, scale x offset by height, not width, since icon to its left
        # is scaled by height, small screen could overlap otherwise
        canvas.create_name_text(
            self._scale_pixels_to_height(36), self._scale_pixels_to_height(16), FONT
        )

        button_x_offset: int = screen_width - icon_size
        HoverableButton(
            canvas, *icon_factory.make_exit_icons(), self.exit, button_x_offset
        )

        button_x_offset -= icon_size
        HoverableButton(
            canvas, *icon_factory.make_minify_icons(), self.minimize, button_x_offset
        )

        button_x_offset -= icon_size
        ToggleButton(
            canvas,
            *icon_factory.make_dropdown_icons(),
            self.handle_dropdown,
            button_x_offset,
        )

        HoverableButton(canvas, *icon_factory.make_trash_icons(), self.trash_image)

        rename_button = HoverableButton(
            canvas, *icon_factory.make_rename_icons(), self.toggle_show_rename_window
        )
        self.rename_button_id: int = rename_button.id

        dropdown_id: int = canvas.create_image(
            screen_width, icon_size, anchor="ne", tag=TOPBAR_TAG, state="hidden"
        )
        self.dropdown = DropdownImage(dropdown_id)

        rename_window_width: int = self._scale_pixels_to_width(250)
        rename_id: int = canvas.create_window(
            0,
            0,
            width=rename_window_width,
            height=int(icon_size * 0.78),
            anchor="nw",
        )
        self.rename_entry = RenameEntry(
            app, canvas, rename_id, rename_window_width, font=FONT
        )
        self.rename_entry.bind("<Return>", self.rename_or_convert)

    def _scale_pixels_to_height(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.height_ratio)

    def _scale_pixels_to_width(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.width_ratio)

    def bring_tk_to_front(self) -> None:
        """Hack to force Tk window to front of screen"""
        self.app.wm_attributes("-topmost", True)
        self.app.update_idletasks()
        self.app.wm_attributes("-topmost", False)

    # Functions handling specific user input

    def handle_canvas_click(self, _: Event) -> None:
        """Toggles the display of topbar when non-topbar area clicked"""
        if self.canvas.is_widget_visible(TOPBAR_TAG):
            self.hide_topbar()
        else:
            self.show_topbar()

    def handle_key(self, event: Event) -> None:
        """Key binds that happen only on main app focus"""
        if event.widget is self.app:
            match event.keycode:
                case Key.LEFT | Key.RIGHT:
                    self.handle_lr_arrow(event)
                case Key.MINUS | Key.EQUALS:
                    self.handle_zoom(event.keycode)
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
            move_amount: int = 1 + (int(event.state) & 5)  # type: ignore
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

    def _load_zoomed_image(
        self, keycode: Literal[Key.MINUS, Key.EQUALS]  # type: ignore
    ) -> None:
        """Function to be called in Tk thread for loading image with zoom"""
        zoom_in: bool = keycode == Key.EQUALS
        new_image: PhotoImage | None = self.image_loader.get_zoomed_image(
            self.file_manager.path_to_image, zoom_in
        )
        if new_image is not None:
            self.canvas.update_image_display(new_image)

    def handle_zoom(
        self, keycode: Literal[Key.MINUS, Key.EQUALS]  # type: ignore
    ) -> None:
        """Handle user input of zooming in or out"""
        if self.animation_id != "":
            return

        if self.image_load_id != "":
            self.app.after_cancel(self.image_load_id)

        self.image_load_id = self.app.after(0, self._load_zoomed_image, keycode)

    # End functions handling specific user input

    def move_to_new_file(self, _: Event) -> None:
        """Moves to a new image from file dialog"""
        moved: bool = self.file_manager.move_to_new_directory()
        if moved:
            self.load_image()

    def exit(self, _: Event | None = None, exit_code: int = 0) -> NoReturn:
        """Safely exits the program"""
        self.image_loader.reset_and_setup()
        self.canvas.delete(self.canvas.file_name_text_id)
        # Dangerous: this prevents an ignored exception since Tk may clean up
        # before PIL does. Lets leave the work to Tk when exiting
        del PhotoImage.__del__
        self.app.quit()
        self.app.destroy()
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
        self.remove_image(True)
        self.load_image_unblocking()

    def hide_rename_window(self) -> None:
        self.canvas.itemconfigure(self.rename_entry.id, state="hidden")
        self.app.focus()

    def toggle_show_rename_window(self, _: Event) -> None:
        if self.canvas.is_widget_visible(self.rename_entry.id):
            self.hide_rename_window()
            return

        if not self.canvas.is_widget_visible(TOPBAR_TAG):
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

        # Cleanup after successful rename
        self.hide_rename_window()
        self.load_image_unblocking()

    def update_after_image_load(self, current_image: PhotoImage) -> None:
        """Updates app title and displayed image"""
        self.canvas.center_image()
        self.canvas.update_image_display(current_image)
        self.app.title(self.file_manager.current_image.name)

    def _load_image_at_current_path(self):
        """Wraps ImageLoader's load call with path from FileManager"""
        return self.image_loader.load_image(self.file_manager.path_to_image)

    def load_image(self) -> None:
        """Loads an image and updates display"""
        self.clear_image()

        # When load fails, keep removing bad image and trying to load next
        while (current_image := self._load_image_at_current_path()) is None:
            self.remove_image(False)

        self.update_after_image_load(current_image)
        if self.canvas.is_widget_visible(TOPBAR_TAG):
            self.update_topbar()

        self.image_load_id = ""

    def load_image_unblocking(self) -> None:
        """Loads an image without blocking main thread"""
        self.dropdown.need_refresh = True
        if self.image_load_id != "":
            self.app.after_cancel(self.image_load_id)
        self.image_load_id = self.app.after(0, self.load_image)

    def show_topbar(self, _: Event | None = None) -> None:
        """Shows all topbar elements and updates its display"""
        self.canvas.itemconfigure(TOPBAR_TAG, state="normal")
        self.update_topbar()

    def hide_topbar(self, _: Event | None = None) -> None:
        """Hides/removes focus from all topbar elements"""
        self.canvas.itemconfigure(TOPBAR_TAG, state="hidden")
        self.hide_rename_window()

    def remove_image(self, delete_from_disk: bool) -> None:
        """Removes current image from internal image list"""
        try:
            self.file_manager.remove_current_image(delete_from_disk)
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

    def animation_loop(self, ms_until_next_frame: int, ms_backoff: int) -> None:
        """Handles looping between animation frames"""
        self.animation_id = self.app.after(
            ms_until_next_frame, self.show_next_frame, ms_backoff
        )

    def show_next_frame(self, ms_backoff: int) -> None:
        """Displays a frame on screen and loops to next frame after a delay"""
        start: float = perf_counter()
        frame: PhotoImage | None
        ms_until_next_frame: int
        frame, ms_until_next_frame = self.image_loader.get_next_frame()

        if frame is None:  # trying to display frame before it is loaded
            ms_until_next_frame = ms_backoff = int(ms_backoff * 1.4)
        else:
            self.canvas.update_image_display(frame)
            elapsed: int = round((perf_counter() - start) * 1000)
            ms_until_next_frame = max(ms_until_next_frame - elapsed, 1)

        self.animation_loop(ms_until_next_frame, ms_backoff)

    def clear_image(self) -> None:
        """Clears all image data"""
        if self.animation_id != "":
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
                details = details[: details.rfind("\n") - 1]
                dropdown.image = create_dropdown_image(details)

            self.canvas.itemconfigure(dropdown.id, image=dropdown.image, state="normal")
        else:
            self.canvas.itemconfigure(dropdown.id, state="hidden")
