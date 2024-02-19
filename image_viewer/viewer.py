import os
from tkinter import Event, Tk
from typing import Final, NoReturn

from PIL.ImageTk import PhotoImage

from factories.icon_factory import IconFactory
from helpers.image_loader import ImageLoader
from helpers.image_resizer import ImageResizer
from managers.file_manager import ImageFileManager
from ui.canvas import CustomCanvas
from ui.rename_entry import RenameEntry
from util.image import DropdownImage
from util.PIL import create_dropdown_image, init_PIL


class ViewerApp:
    """Main UI class handling IO and on screen widgets"""

    __slots__ = (
        "animation_id",
        "app",
        "canvas",
        "dropdown",
        "dropdown_button_id",
        "dropdown_hidden_icon",
        "dropdown_hidden_icon_hovered",
        "dropdown_showing_icon",
        "dropdown_showing_icon_hovered",
        "file_manager",
        "height_ratio",
        "image_loader",
        "image_load_id",
        "move_id",
        "need_to_redraw",
        "rename_button_id",
        "rename_entry",
        "rename_window_x_offset",
        "width_ratio",
    )

    def __init__(self, first_image_to_show: str, path_to_exe: str) -> None:
        self.file_manager = ImageFileManager(first_image_to_show)

        # UI varaibles
        self.need_to_redraw: bool = False
        self.rename_window_x_offset: int = 0
        self.move_id: str = ""
        self.image_load_id: str = ""
        self.animation_id: str = ""

        # Application and canvas
        app = Tk()
        self.app = app
        app.attributes("-fullscreen", True)
        canvas = CustomCanvas(app)
        self.canvas = canvas

        if os.name == "nt":
            app.state("zoomed")
            app.wm_iconbitmap(default=os.path.join(path_to_exe, "icon/icon.ico"))
        else:
            from tkinter import Image as tkImage

            app.wm_iconbitmap(
                bitmap=tkImage("photo", file=os.path.join(path_to_exe, "icon/icon.png"))
            )

        self.height_ratio: Final[float] = canvas.screen_height / 1080
        self.width_ratio: Final[float] = canvas.screen_width / 1920

        self._load_assests(
            app, canvas, canvas.screen_width, self._scale_pixels_to_height(32)
        )

        # set up and draw first image, then get all image paths in directory
        self.image_loader = ImageLoader(
            self.file_manager,
            ImageResizer(canvas.screen_width, canvas.screen_height, path_to_exe),
            self.animation_loop,
        )

        init_PIL(self._scale_pixels_to_height(22))

        # Don't call this class's load_image here since we only loaded one image
        # and if its failed to load, we don't want to exit. Special check for that here
        if (current_image := self.image_loader.load_image()) is not None:
            self.update_after_image_load(current_image)
            app.update()

        self.file_manager.fully_load_image_data()

        # if first load failed, load new one now that all images are loaded
        if current_image is None:
            self.load_image()

        self.canvas.tag_bind("back", "<Button-1>", self.handle_canvas_click)
        self._add_keybinds()

        app.mainloop()

    def _add_keybinds(self) -> None:
        """Assigns OS generic keybinds to app"""
        app = self.app
        app.bind("<FocusIn>", self.redraw)
        app.bind("<Escape>", self.handle_esc)
        app.bind("<KeyPress>", self.handle_key)
        app.bind("<KeyRelease>", self.handle_key_release)
        app.bind("<Control-r>", self.refresh)
        app.bind("<Control-d>", lambda _: self.file_manager.show_image_details())
        app.bind("<F2>", self.toggle_show_rename_window)
        app.bind("<F5>", lambda _: self.load_image_unblocking())
        app.bind("<Up>", self.hide_topbar)
        app.bind("<Down>", self.show_topbar)
        app.bind("<Alt-Left>", self.handle_alt_arrow_keys)
        app.bind("<Alt-Right>", self.handle_alt_arrow_keys)
        app.bind("<Alt-Up>", self.handle_alt_arrow_keys)
        app.bind("<Alt-Down>", self.handle_alt_arrow_keys)

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

        topbar_height += topbar_height % 2  # ensure even number

        # negative makes it an absolute size for consistency with different monitors
        FONT: str = f"arial -{self._scale_pixels_to_height(18)}"

        icon_factory = IconFactory(topbar_height)

        canvas.create_topbar(icon_factory.make_topbar(screen_width))
        # weird case, scale x offset by height, not width, since icon to its left
        # is scaled by height, small screen could overlap otherwise
        canvas.create_name_text(
            self._scale_pixels_to_height(36), self._scale_pixels_to_height(16), FONT
        )

        canvas.make_topbar_button(  # type: ignore
            *icon_factory.make_exit_icons(), "ne", screen_width, self.exit
        )
        canvas.make_topbar_button(  # type: ignore
            *icon_factory.make_minify_icons(),
            "ne",
            screen_width - topbar_height,
            self.minimize,
        )
        canvas.make_topbar_button(  # type: ignore
            *icon_factory.make_trash_icons(), "nw", 0, self.trash_image
        )
        self.rename_button_id: int = canvas.make_topbar_button(  # type: ignore
            *icon_factory.make_rename_icons(),
            "nw",
            0,
            self.toggle_show_rename_window,
        )

        # details dropdown
        (
            self.dropdown_hidden_icon,
            self.dropdown_showing_icon,
            self.dropdown_hidden_icon_hovered,
            self.dropdown_showing_icon_hovered,
        ) = icon_factory.make_dropdown_icons()

        self.dropdown_button_id: int = canvas.create_image(
            screen_width - (topbar_height << 1),
            0,
            image=self.dropdown_hidden_icon,
            anchor="ne",
            tag="topbar",
            state="hidden",
        )
        canvas.tag_bind(
            self.dropdown_button_id, "<ButtonRelease-1>", self.handle_dropdown
        )
        canvas.tag_bind(self.dropdown_button_id, "<Enter>", self.hover_dropdown_toggle)
        canvas.tag_bind(
            self.dropdown_button_id, "<Leave>", self.leave_hover_dropdown_toggle
        )
        dropdown_id: int = canvas.create_image(
            screen_width, topbar_height, anchor="ne", tag="topbar", state="hidden"
        )
        self.dropdown = DropdownImage(dropdown_id)

        rename_window_width: int = self._scale_pixels_to_width(250)
        rename_id: int = canvas.create_window(
            0,
            0,
            width=rename_window_width,
            height=int(topbar_height * 0.78),
            anchor="nw",
        )
        self.rename_entry = RenameEntry(  # TODO: move this to canvas?
            app, canvas, rename_id, rename_window_width, font=FONT
        )
        self.rename_entry.bind("<Return>", self.try_rename_or_convert)
        canvas.itemconfigure(rename_id, state="hidden", window=self.rename_entry)

    def _scale_pixels_to_height(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.height_ratio)

    def _scale_pixels_to_width(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.width_ratio)

    # Functions handling user input

    def handle_canvas_click(self, _: Event) -> None:
        """Toggles the display of topbar when non-topbar area clicked"""
        if self.canvas.is_widget_visible("topbar"):
            self.hide_topbar()
        else:
            self.show_topbar()

    def handle_key(self, event: Event) -> None:
        """Key binds on main screen"""
        if event.widget is self.app:
            match event.keycode:
                case 37 | 39:  # Left/Right arrow
                    self.handle_lr_arrow(event)
                case 187 | 189:  # - or =
                    self.handle_zoom(event)
                case 82:  # r
                    self.toggle_show_rename_window(event)

    def handle_key_release(self, event: Event) -> None:
        """Handle key release, current just used for L/R arrow release"""
        if self.move_id != "" and event.keycode in (37, 39):  # Left/Right
            self.app.after_cancel(self.move_id)
            self.move_id = ""

    def handle_lr_arrow(self, event: Event) -> None:
        """Handle L/R arrow key input
        Doesn't move when main window unfocused"""
        if self.move_id == "":
            # move +4 when ctrl held, +1 when shift held
            move_amount: int = 1 + (int(event.state) & 5)  # type: ignore
            if event.keysym == "Left":
                move_amount = -move_amount
            self.move(move_amount)
            self._repeat_move(move_amount, 500)

    def _repeat_move(self, move_amount: int, ms: int) -> None:
        """Repeat move to next image while L/R key held"""
        if self.move_id != "":
            self.move(move_amount)
            self.move_id = self.app.after(ms, self._repeat_move, move_amount, 200)

    def handle_alt_arrow_keys(self, event: Event) -> None:
        """Wraps canvas's event handler if app is focused"""
        if event.widget is self.app:
            self.canvas.handle_alt_arrow_keys(event.keycode)

    def handle_esc(self, _: Event) -> None:
        """Closes rename window, then program on hitting escape"""
        if self.canvas.is_widget_visible(self.rename_entry.id):
            self.hide_rename_window()
            return
        self.exit()

    def handle_dropdown(self, _: Event) -> None:
        """Handle when user clicks on the dropdown arrow"""
        self.dropdown.toggle_display()
        self.hover_dropdown_toggle()  # fake mouse hover
        self.update_details_dropdown()

    def _load_zoomed_image(self, keycode: int) -> None:
        """Function to be called in Tk thread for loading image with zoom"""
        new_image: PhotoImage | None = self.image_loader.get_zoomed_image(keycode)
        if new_image is not None:
            self.canvas.update_img_display(new_image, False)

    def handle_zoom(self, event: Event) -> None:
        """Handle user input of zooming in or out"""
        if self.animation_id != "":
            return

        if self.image_load_id != "":
            self.app.after_cancel(self.image_load_id)
        self.image_load_id = self.app.after(0, self._load_zoomed_image, event.keycode)

    # End functions handling user input

    def exit(self, _: Event | None = None) -> NoReturn:
        """Safely exits the program"""
        self.image_loader.reset_and_setup()
        self.canvas.delete(self.canvas.file_name_text_id)
        # Dangerous: this prevents an ignored exception since Tk may clean up
        # before PIL does. Lets leave the work to Tk when exiting
        del PhotoImage.__del__
        self.app.quit()
        self.app.destroy()
        raise SystemExit(0)  # I used exit(0) here, but didn't work with --standalone

    def minimize(self, _: Event) -> None:
        """Minimizes the app and sets flag to redraw current image when opened again"""
        self.need_to_redraw = True
        self.app.iconify()
        if self.move_id != "":
            self.app.after_cancel(self.move_id)

    def refresh(self, _: Event) -> None:
        """Gets images in current directory and update internal list with them"""
        self.clear_animation_variables()
        try:
            self.file_manager.refresh_image_list()
        except IndexError:
            self.exit()
        self.load_image_unblocking()

    def move(self, amount: int) -> None:
        """Moves to different image
        amount: any non-zero value indicating movement to next or previous"""
        self.hide_rename_window()
        self.file_manager.move_index(amount)
        self.load_image_unblocking()

    def redraw(self, event: Event) -> None:
        """Redraws screen if current image has a diffent size than when it was loaded,
        implying it was edited outside of the program"""
        if event.widget is not self.app or not self.need_to_redraw:
            return
        self.need_to_redraw = False
        if self.file_manager.current_image_cache_still_fresh():
            return
        self.load_image_unblocking()

    def trash_image(self, _: Event | None = None) -> None:
        """Move current image to trash and moves to next"""
        self.clear_animation_variables()
        self.hide_rename_window()
        self.remove_image(True)
        self.load_image_unblocking()

    def hide_rename_window(self) -> None:
        self.canvas.itemconfigure(self.rename_entry.id, state="hidden")
        self.app.focus()

    def leave_hover_dropdown_toggle(self, _: Event | None = None) -> None:
        self.canvas.itemconfigure(
            self.dropdown_button_id,
            image=(
                self.dropdown_showing_icon
                if self.dropdown.showing
                else self.dropdown_hidden_icon
            ),
        )

    def hover_dropdown_toggle(self, _: Event | None = None) -> None:
        self.canvas.itemconfigure(
            self.dropdown_button_id,
            image=(
                self.dropdown_showing_icon_hovered
                if self.dropdown.showing
                else self.dropdown_hidden_icon_hovered
            ),
        )

    def toggle_show_rename_window(self, _: Event) -> None:
        canvas = self.canvas
        if canvas.is_widget_visible(self.rename_entry.id):
            self.hide_rename_window()
            return

        if not canvas.is_widget_visible("topbar"):
            self.show_topbar()

        canvas.itemconfigure(self.rename_entry.id, state="normal")
        # x offset for topbar items scaled by height, not width
        canvas.coords(
            self.rename_entry.id,
            self.rename_window_x_offset + self._scale_pixels_to_height(40),
            self._scale_pixels_to_height(4),
        )
        self.rename_entry.focus()

    def try_rename_or_convert(self, _: Event) -> None:
        """Handles user input into rename window.
        Trys to convert or rename based on input"""
        try:
            self.file_manager.rename_or_convert_current_image(self.rename_entry.get())
        except Exception:  # pylint: disable=broad-exception-caught
            self.rename_entry.error_flash()
            return

        # Cleanup after successful rename
        self.hide_rename_window()
        self.load_image()
        self.refresh_topbar()

    def update_after_image_load(self, current_image: PhotoImage) -> None:
        """Updates app title and displayed image"""
        self.canvas.update_img_display(current_image, True)
        self.app.title(self.file_manager.current_image.name)

    def load_image(self) -> None:
        """Loads an image and updates display"""
        self.clear_animation_variables()

        # When load fails, keep removing bad image and trying to load next
        while (current_image := self.image_loader.load_image()) is None:
            self.remove_image(False)

        self.update_after_image_load(current_image)
        if self.canvas.is_widget_visible("topbar"):
            self.refresh_topbar()
        self.image_load_id = ""

    def load_image_unblocking(self) -> None:
        """Loads an image without blocking main thread"""
        self.dropdown.need_refresh = True
        if self.image_load_id != "":
            self.app.after_cancel(self.image_load_id)
        self.image_load_id = self.app.after(0, self.load_image)

    def show_topbar(self, _: Event | None = None) -> None:
        """Shows all topbar elements and updates its display"""
        self.canvas.itemconfigure("topbar", state="normal")
        self.refresh_topbar()

    def hide_topbar(self, _: Event | None = None) -> None:
        """Hides/removes focus from all topbar elements"""
        self.canvas.itemconfigure("topbar", state="hidden")
        self.hide_rename_window()

    def remove_image(self, delete_from_disk: bool) -> None:
        """Removes current image from internal image list"""
        try:
            self.file_manager.remove_current_image(delete_from_disk)
        except IndexError:
            self.exit()

    def refresh_topbar(self) -> None:
        """Updates all elements on the topbar with current info"""
        self.rename_window_x_offset = self.canvas.refresh_text(
            self.file_manager.current_image.name
        )
        self.canvas.coords(self.rename_button_id, self.rename_window_x_offset, 0)

        self.update_details_dropdown()

    def animation_loop(self, ms_until_next_frame: int, ms_backoff: int) -> None:
        """Handles looping between animation frames"""
        self.animation_id = self.app.after(
            ms_until_next_frame, self.animate, ms_backoff
        )

    def animate(self, ms_backoff: int) -> None:
        """Displays a frame on screen and loops to next frame after a delay"""
        frame_and_speed = self.image_loader.get_next_frame()

        # if tried to show next frame before it is loaded
        # reset to current frame and try again after delay
        ms_until_next_frame: int
        if frame_and_speed is None:
            ms_backoff = int(ms_backoff * 1.4)
            ms_until_next_frame = ms_backoff
        else:
            self.canvas.update_img_display(frame_and_speed[0], False)
            ms_until_next_frame = frame_and_speed[1]

        self.animation_loop(ms_until_next_frame, ms_backoff)

    def clear_animation_variables(self) -> None:
        """Clears all animation data"""
        if self.animation_id == "":
            return

        self.app.after_cancel(self.animation_id)
        self.animation_id = ""
        self.image_loader.reset_and_setup()

    def update_details_dropdown(self) -> None:
        """Updates the infomation and state of dropdown image"""
        dropdown = self.dropdown
        if dropdown.showing:
            if dropdown.need_refresh:
                try:
                    dimension_text, size_text, _ = (
                        self.file_manager.get_cached_details()
                    )
                except KeyError:
                    return  # data not present in cache

                dropdown.image = create_dropdown_image(dimension_text, size_text)

            self.canvas.itemconfigure(dropdown.id, image=dropdown.image, state="normal")
        else:
            self.canvas.itemconfigure(dropdown.id, state="hidden")
