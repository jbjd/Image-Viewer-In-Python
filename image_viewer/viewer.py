import os
from tkinter import Canvas, Event, Tk
from tkinter.messagebox import askyesno

from PIL.ImageTk import PhotoImage

from factories.icon_factory import IconFactory
from helpers.image_loader import ImageLoader
from managers.file_manager import ImageFileManager
from ui.rename_entry import RenameEntry
from util.image import CachedImageData, DropdownImage, create_dropdown_image, init_PIL


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
        "dropdown_shown",
        "file_manager",
        "file_name_text_id",
        "height_ratio",
        "image_display_id",
        "image_loader",
        "move_id",
        "redraw_screen",
        "rename_button_id",
        "rename_entry",
        "rename_window_id",
        "rename_window_x_offset",
        "topbar",
        "topbar_shown",
        "width_ratio",
    )

    def __init__(self, first_image_to_show: str, path_to_exe: str) -> None:
        self.file_manager = ImageFileManager(first_image_to_show)

        # UI varaibles
        self.topbar_shown: bool
        self.dropdown_shown: bool
        self.redraw_screen: bool
        self.topbar_shown = self.dropdown_shown = self.redraw_screen = False
        self.rename_window_x_offset: int = 0
        self.move_id: str = ""

        # Animation variables
        self.animation_id: str = ""

        # Application and canvas
        app = Tk()
        canvas = Canvas(app, bg="black", highlightthickness=0)
        canvas.pack(anchor="nw", fill="both", expand=1)
        app.attributes("-fullscreen", True)
        self.app = app
        self.canvas = canvas

        is_windows: bool = os.name == "nt"
        if is_windows:
            app.state("zoomed")
            app.wm_iconbitmap(default=os.path.join(path_to_exe, "icon/icon.ico"))
        else:
            from tkinter import Image as tkImage

            app.tk.call(
                "wm",
                "iconphoto",
                app._w,  # type: ignore
                tkImage("photo", file=os.path.join(path_to_exe, "icon/icon.png")),
            )

        app.update()  # updates winfo width and height to the current size
        screen_width: int = app.winfo_width()
        screen_height: int = app.winfo_height()
        self.height_ratio: float = screen_height / 1080
        self.width_ratio: float = screen_width / 1920
        canvas.create_rectangle(
            0, 0, screen_width, screen_height, fill="black", tag="back"
        )
        self.image_display_id = canvas.create_image(
            screen_width >> 1, screen_height >> 1, anchor="center", tag="back"
        )
        self._load_assests(app, canvas, screen_width, self._scale_pixels_to_height(32))

        # set up and draw first image, then get all image paths in directory
        self.image_loader = ImageLoader(
            self.file_manager,
            screen_width,
            screen_height,
            path_to_exe,
            self.animation_loop,
        )

        # Don't call load_image for first image since if it fails to load, don't exit
        # until we load the rest of the images and try to display them as well
        if current_image := self.image_loader.load_image():
            self.update_after_image_load(current_image)

        app.update()
        self.file_manager.fully_load_image_data()

        # if first load failed, load new one now that all images are loaded
        if current_image is None:
            self.load_image()

        init_PIL(self._scale_pixels_to_height(22))

        canvas.tag_bind("back", "<Button-1>", self.handle_canvas_click)
        app.bind("<FocusIn>", self.redraw)
        app.bind("<Escape>", self.handle_esc)
        app.bind("<KeyPress>", self.handle_key)
        app.bind("<KeyRelease>", self.handle_key_release)
        app.bind("<Control-r>", self.refresh)
        app.bind("<F2>", self.toggle_show_rename_window)
        app.bind("<Up>", self.hide_topbar)
        app.bind("<Down>", self.show_topbar)
        app.bind("<Left>", self.handle_lr_arrow)
        app.bind("<Right>", self.handle_lr_arrow)

        if is_windows:
            app.bind(
                "<MouseWheel>", lambda event: self.move(-1 if event.delta > 0 else 1)
            )
        else:
            app.bind("<Button-4>", lambda _: self.move(-1))
            app.bind("<Button-5>", lambda _: self.move(1))

        app.mainloop()

    def _load_assests(
        self, app: Tk, canvas: Canvas, screen_width: int, topbar_height: int
    ) -> None:
        """
        Load all assets on topbar from factory and create tkinter objects
        topbar_height: size to make icons/topbar
        """

        def _make_topbar_button(
            canvas: Canvas,
            regular_image: PhotoImage,
            hovered_image: PhotoImage,
            anchor: str,
            x_offset: int,
            function_to_bind,
        ) -> int:
            """Default way to setup a button on the topbar"""
            button_id: int = canvas.create_image(
                x_offset,
                0,
                image=regular_image,
                anchor=anchor,
                tag="topbar",
                state="hidden",
            )

            canvas.tag_bind(
                button_id,
                "<Enter>",
                lambda _: canvas.itemconfig(button_id, image=hovered_image),
            )
            canvas.tag_bind(
                button_id,
                "<Leave>",
                lambda _: canvas.itemconfig(button_id, image=regular_image),
            )
            canvas.tag_bind(button_id, "<ButtonRelease-1>", function_to_bind)
            return button_id

        topbar_height += topbar_height % 2  # ensure even number

        # negative makes it an absolute size for consistency with different monitors
        FONT: str = f"arial -{self._scale_pixels_to_height(18)}"

        icon_factory = IconFactory(topbar_height)

        # create the topbar
        self.topbar = icon_factory.make_topbar(screen_width)
        canvas.create_image(
            0, 0, image=self.topbar, anchor="nw", tag="topbar", state="hidden"
        )
        self.file_name_text_id: int = canvas.create_text(
            self._scale_pixels_to_width(36),
            self._scale_pixels_to_height(16),
            text="",
            fill="white",
            anchor="w",
            font=FONT,
            tags="topbar",
        )
        _make_topbar_button(  # type: ignore
            canvas, *icon_factory.make_exit_icons(), "ne", screen_width, self.exit
        )
        _make_topbar_button(  # type: ignore
            canvas,
            *icon_factory.make_minify_icons(),
            "ne",
            screen_width - topbar_height,
            self.minimize,
        )
        _make_topbar_button(  # type: ignore
            canvas, *icon_factory.make_trash_icons(), "nw", 0, self.trash_image
        )
        self.rename_button_id: int = _make_topbar_button(  # type: ignore
            canvas,
            *icon_factory.make_rename_icons(),
            "nw",
            0,
            self.toggle_show_rename_window,
        )

        # details dropdown
        (
            self.dropdown_hidden_icon,
            self.dropdown_hidden_icon_hovered,
            self.dropdown_showing_icon,
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
        self.dropdown = DropdownImage(
            canvas.create_image(
                screen_width, topbar_height, anchor="ne", tag="topbar", state="hidden"
            )
        )

        # rename window
        self.rename_window_id: int = canvas.create_window(
            0,
            0,
            width=self._scale_pixels_to_width(200),
            height=int(topbar_height * 0.75),
            anchor="nw",
        )
        self.rename_entry = RenameEntry(app, font=FONT)
        self.rename_entry.bind("<Return>", self.try_rename_or_convert)
        canvas.itemconfig(
            self.rename_window_id, state="hidden", window=self.rename_entry
        )

    def _scale_pixels_to_height(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.height_ratio)

    def _scale_pixels_to_width(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.width_ratio)

    # Functions handling user input

    def handle_canvas_click(self, _: Event) -> None:
        """toggles the display of topbar when non-topbar area clicked"""
        if self.topbar_shown:
            self.hide_topbar()
        else:
            self.show_topbar()

    def handle_key(self, event: Event) -> None:
        """Key binds on main screen"""
        if event.widget is self.app:
            if event.keysym == "r":
                self.toggle_show_rename_window(event)

    def handle_key_release(self, event: Event) -> None:
        if event.widget is self.app:
            if self.move_id and event.keysym in ("Left", "Right"):
                self.app.after_cancel(self.move_id)
                self.move_id = ""

    def handle_lr_arrow(self, event: Event) -> None:
        """Handle L/R arrow key input
        Doesn't move when main window unfocused"""
        if event.widget is self.app and self.move_id == "":
            # move +4 when ctrl held, +1 when shift held
            move_amount: int = 1 + (event.state & 5)  # type: ignore
            if event.keysym == "Left":
                move_amount = -move_amount
            self._repeat_move(move_amount, 600)

    def _repeat_move(self, move_amount: int, ms: int) -> None:
        """Repeat move to next image while L/R key held"""
        self.move(move_amount)
        self.move_id = self.app.after(ms, self._repeat_move, move_amount, 200)

    def handle_esc(self, _: Event) -> None:
        """Closes rename window, then program on hitting escape"""
        if self.canvas.itemcget(self.rename_window_id, "state") == "normal":
            self.hide_rename_window()
            return
        self.exit()

    def handle_dropdown(self, _: Event) -> None:
        """Handle when user clicks on the dropdown arrow"""
        self.dropdown_shown = not self.dropdown_shown
        self.hover_dropdown_toggle()  # fake mouse hover
        self.update_details_dropdown()

    # End functions handling user input

    def exit(self, _: Event | None = None) -> None:
        """Safely exits the program"""
        self.image_loader.reset()
        self.canvas.delete(self.file_name_text_id)
        self.app.quit()
        self.app.destroy()
        raise SystemExit(0)  # I used exit(0) here, but didn't work with --standalone

    def minimize(self, _: Event) -> None:
        """Minimizes the app and sets flag to redraw current image when opened again"""
        self.redraw_screen = True
        self.app.iconify()

    def refresh(self, _: Event) -> None:
        """Get images in current directory and update internal list with them"""
        self.clear_animation_variables()
        try:
            self.file_manager.refresh_image_list()
        except IndexError:
            self.exit()

        self.load_image()

    def move(self, amount: int) -> None:
        """
        Move to different image
        amount: any non-zero value indicating movement to next or previous
        """
        self.hide_rename_window()
        self.file_manager.move_current_index(amount)
        self.dropdown.refresh = True

        self.load_image()
        if self.topbar_shown:
            self.refresh_topbar()

    def redraw(self, event: Event) -> None:
        """
        Redraws screen if current image has a diffent size than when it was loaded
        This implys it was edited outside of the program
        """
        if event.widget is not self.app or not self.redraw_screen:
            return
        self.redraw_screen = False
        if self.file_manager.current_image_cache_still_fresh():
            return
        self.load_image()

    def trash_image(self, _: Event | None = None) -> None:
        """Move current image to trash and moves to next"""
        self.clear_animation_variables()
        self.hide_rename_window()
        self.remove_image_and_move_to_next(True)

    def hide_rename_window(self) -> None:
        self.canvas.itemconfig(self.rename_window_id, state="hidden")
        self.app.focus()

    def leave_hover_dropdown_toggle(self, _: Event | None = None) -> None:
        self.canvas.itemconfig(
            self.dropdown_button_id,
            image=self.dropdown_showing_icon
            if self.dropdown_shown
            else self.dropdown_hidden_icon,
        )

    def hover_dropdown_toggle(self, _: Event | None = None) -> None:
        self.canvas.itemconfig(
            self.dropdown_button_id,
            image=self.dropdown_showing_icon_hovered
            if self.dropdown_shown
            else self.dropdown_hidden_icon_hovered,
        )

    def toggle_show_rename_window(self, _: Event | None = None) -> None:
        canvas = self.canvas
        if canvas.itemcget(self.rename_window_id, "state") == "normal":
            self.hide_rename_window()
            return

        if canvas.itemcget("topbar", "state") == "hidden":
            self.show_topbar()

        canvas.itemconfig(self.rename_window_id, state="normal")
        canvas.coords(
            self.rename_window_id,
            self.rename_window_x_offset + self._scale_pixels_to_width(40),
            self._scale_pixels_to_height(4),
        )
        self.rename_entry.focus()

    def _ask_delete_after_convert(self, new_format: str) -> None:
        """Used as callback function for after a succecssful file conversion"""
        if askyesno(
            "Confirm deletion",
            f"Converted file to {new_format}, delete old file?",
        ):
            self.remove_image_and_move_to_next(True)

    def try_rename_or_convert(self, _: Event) -> None:
        """Handles user input into rename window.
        Trys to convert or rename based on input"""
        try:
            self.file_manager.rename_or_convert_current_image(
                self.rename_entry.get(),
                self._ask_delete_after_convert,
            )
        except Exception:
            self.rename_entry.error_flash()
            return

        # Cleanup after successful rename
        self.hide_rename_window()
        self.load_image()
        self.refresh_topbar()

    def update_after_image_load(self, current_image: PhotoImage) -> None:
        """Updates app title and displayed image"""
        self.canvas.itemconfig(self.image_display_id, image=current_image)
        self.app.title(self.file_manager.current_image.name)

    def load_image(self) -> None:
        """Loads an image and updates display"""
        self.clear_animation_variables()

        # When load fails, keep removing bad image and trying to load next
        while (current_image := self.image_loader.load_image()) is None:
            self.remove_image(False)

        self.update_after_image_load(current_image)

    def show_topbar(self, _: Event | None = None) -> None:
        """Shows all topbar elements and updates its display"""
        self.topbar_shown = True
        self.canvas.itemconfig("topbar", state="normal")
        self.refresh_topbar()

    def hide_topbar(self, _: Event | None = None) -> None:
        """Hides/removes focus from all topbar elements"""
        self.topbar_shown = False
        self.canvas.itemconfig("topbar", state="hidden")
        self.hide_rename_window()

    def remove_image(self, delete_from_disk: bool) -> None:
        """Removes current image from internal image list"""
        try:
            self.file_manager.remove_current_image(delete_from_disk)
        except IndexError:
            self.exit()

    def remove_image_and_move_to_next(self, delete_from_disk: bool) -> None:
        """Removes current image from internal image list
        and optionaly deletes it from disk"""
        self.remove_image(delete_from_disk)

        self.load_image()
        if self.topbar_shown:
            self.refresh_topbar()

    def refresh_topbar(self) -> None:
        """Updates all elements on the topbar with current info"""
        self.canvas.itemconfig(
            self.file_name_text_id, text=self.file_manager.current_image.name
        )
        self.rename_window_x_offset = self.canvas.bbox(self.file_name_text_id)[2]
        self.canvas.coords(self.rename_button_id, self.rename_window_x_offset, 0)

        self.update_details_dropdown()

    def animation_loop(self, ms_until_next_frame: int, ms_backoff: int) -> None:
        """Handles looping between animation frames"""
        self.animation_id = self.app.after(
            ms_until_next_frame, self.animate, ms_backoff
        )

    def animate(self, ms_backoff: int) -> None:
        """displays a frame on screen and loops to next frame after a delay"""
        frame_and_speed = self.image_loader.get_next_frame()

        # if tried to show next frame before it is loaded
        # reset to current frame and try again after delay
        ms_until_next_frame: int
        if frame_and_speed is None:
            ms_backoff = int(ms_backoff * 1.4)
            ms_until_next_frame = ms_backoff
        else:
            self.canvas.itemconfig(self.image_display_id, image=frame_and_speed[0])
            ms_until_next_frame = frame_and_speed[1]

        self.animation_loop(ms_until_next_frame, ms_backoff)

    def clear_animation_variables(self) -> None:
        """Clears all animation data"""
        if self.animation_id == "":
            return

        self.app.after_cancel(self.animation_id)
        self.animation_id = ""
        self.image_loader.reset()

    def update_details_dropdown(self) -> None:
        """Updates the infomation and state of dropdown image"""
        dropdown = self.dropdown
        if self.dropdown_shown:
            if dropdown.refresh:
                image_info: CachedImageData = (
                    self.file_manager.get_current_image_cache()
                )
                dimension_text: str = f"Pixels: {image_info.width}x{image_info.height}"
                size_text: str = f"Size: {image_info.dimensions}"

                dropdown.image = create_dropdown_image(dimension_text, size_text)

            self.canvas.itemconfig(dropdown.id, image=dropdown.image, state="normal")
        else:
            self.canvas.itemconfig(dropdown.id, state="hidden")
