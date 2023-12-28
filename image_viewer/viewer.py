import os
import tkinter
from collections.abc import Callable
from tkinter import Canvas, Entry, Event, Tk
from tkinter.messagebox import askyesno
from typing import Optional

from PIL.ImageTk import PhotoImage

from factories.icon_factory import IconFactory
from helpers.image_loader import ImageLoader
from managers.file_manager import ImageFileManager
from util.image import CachedImageData, create_dropdown_image, init_font


class ViewerApp:
    __slots__ = (
        "animation_id",
        "app",
        "canvas",
        "dropdown_button_id",
        "dropdown_hidden_icon",
        "dropdown_hidden_icon_hovered",
        "dropdown_id",
        "dropdown_image",
        "dropdown_showing_icon",
        "dropdown_showing_icon_hovered",
        "dropdown_shown",
        "file_manager",
        "file_name_text_id",
        "image_display_id",
        "image_loader",
        "key_bindings",
        "move_id",
        "redraw_screen",
        "rename_button_id",
        "rename_entry",
        "rename_window_id",
        "rename_window_x_offset",
        "size_ratio",
        "topbar",
        "topbar_shown",
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

        # application and canvas
        self.app = Tk()
        self.canvas = Canvas(self.app, bg="black", highlightthickness=0)
        self.canvas.pack(anchor="nw", fill="both", expand=1)
        self.app.attributes("-fullscreen", True)

        # Set icon and zoom state
        if os.name == "nt":
            self.app.state("zoomed")
            self.app.wm_iconbitmap(default=os.path.join(path_to_exe, "icon/icon.ico"))
        else:
            self.app.tk.call(
                "wm",
                "iconphoto",
                self.app._w,  # type: ignore
                tkinter.Image("photo", file=os.path.join(path_to_exe, "icon/icon.png")),
            )

        self.app.update()  # updates winfo width and height to the current size
        screen_width: int = self.app.winfo_width()
        screen_height: int = self.app.winfo_height()
        self.size_ratio: float = screen_height / 1080
        background = self.canvas.create_rectangle(
            0, 0, screen_width, screen_height, fill="black"
        )
        self.image_display_id = self.canvas.create_image(
            screen_width >> 1, screen_height >> 1, anchor="center"
        )
        self.load_assests(screen_width, self.scale_pixels_to_screen(32))

        # set up and draw first image, then get all image paths in directory
        self.image_loader = ImageLoader(
            self.file_manager,
            screen_width,
            screen_height,
            path_to_exe,
            self.animation_loop,
        )

        self.load_image()
        self.app.update()
        self.file_manager.fully_load_image_data()
        init_font(self.scale_pixels_to_screen(22))

        # events based on input
        self.key_bindings: dict[str, Callable] = {
            "F2": self.toggle_show_rename_window,
            "Up": self.hide_topbar,
            "Down": self.show_topbar,
            "Left": self.lr_arrow,
            "Right": self.lr_arrow,
        }  # allowed in entry or main app
        self.canvas.tag_bind(background, "<Button-1>", self.handle_click)
        self.canvas.tag_bind(self.image_display_id, "<Button-1>", self.handle_click)
        self.app.bind("<FocusIn>", self.redraw)
        self.app.bind("<Escape>", self.escape_button)
        self.app.bind("<KeyPress>", self.handle_keybinds_main)
        self.app.bind("<KeyRelease>", self.handle_key_release)

        if os.name == "nt":
            self.app.bind(
                "<MouseWheel>", lambda event: self.move(-1 if event.delta > 0 else 1)
            )
        else:
            self.app.bind("<Button-4>", lambda _: self.move(-1))
            self.app.bind("<Button-5>", lambda _: self.move(1))

        self.app.mainloop()

    def scale_pixels_to_screen(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.size_ratio)

    def handle_key_release(self, event: Event) -> None:
        if event.widget is self.app:
            if self.move_id and (event.keysym == "Left" or event.keysym == "Right"):
                self.app.after_cancel(self.move_id)
                self.move_id = ""

    def handle_keybinds_main(self, event: Event) -> None:
        """Key binds on main screen"""
        if event.widget is self.app:
            if event.keysym == "r":
                self.toggle_show_rename_window(event)
            else:
                self.handle_keybinds_default(event)

    def handle_keybinds_default(self, event: Event) -> None:
        """Key binds that can be used anywhere"""
        if event.keysym in self.key_bindings:
            self.key_bindings[event.keysym](event)

    def lr_arrow(self, event: Event) -> None:
        """Handle L/R arrow key input
        Doesn't move when main window unfocused"""
        if self.move_id != "":
            return
        if event.widget is self.app:
            # move +4 when ctrl held, +1 when shift held
            move_amount: int = 1 + (event.state & 5)  # type: ignore
            if event.keysym == "Left":
                move_amount = -move_amount
            self.repeat_move(move_amount, 600)

    def repeat_move(self, move_amount: int, ms: int) -> None:
        """Repeat move to next image while L/R key held"""
        self.move(move_amount)
        self.move_id = self.app.after(ms, self.repeat_move, move_amount, 200)

    def hide_rename_window(self) -> None:
        self.canvas.itemconfig(self.rename_window_id, state="hidden")
        self.app.focus()

    def move(self, amount: int) -> None:
        """
        Move to different image
        amount: any non-zero value indicating movement to next or previous
        """
        self.hide_rename_window()
        self.file_manager.move_current_index(amount)

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

    def load_assests(self, screen_width: int, topbar_height: int) -> None:
        """
        Load all assets on topbar from factory and create tkinter objects
        topbar_height: size to make icons/topbar
        """
        FONT: str = "arial 11"

        icon_factory = IconFactory(topbar_height)
        self.topbar = icon_factory.make_topbar(screen_width)

        exit_icon = icon_factory.make_exit_icon()
        exit_icon_hovered = icon_factory.make_exit_icon_hovered()

        minify_icon, minify_icon_hovered = icon_factory.make_minify_icons()

        trash_icon, trash_icon_hovered = icon_factory.make_trash_icons()

        (
            self.dropdown_hidden_icon,
            self.dropdown_hidden_icon_hovered,
        ) = icon_factory.make_dropdown_hidden_icons()

        (
            self.dropdown_showing_icon,
            self.dropdown_showing_icon_hovered,
        ) = icon_factory.make_dropdown_showing_icons()

        rename_icon, rename_icon_hovered = icon_factory.make_rename_icons()

        # create the topbar
        self.canvas.create_image(
            0, 0, image=self.topbar, anchor="nw", tag="topbar", state="hidden"
        )
        self.file_name_text_id: int = self.canvas.create_text(
            36.0,
            5.0,
            text="",
            fill="white",
            anchor="nw",
            font=FONT,
            tags="topbar",
        )
        self.make_topbar_button(
            exit_icon, exit_icon_hovered, "ne", screen_width, self.exit
        )
        self.make_topbar_button(
            minify_icon,
            minify_icon_hovered,
            "ne",
            screen_width - topbar_height,
            self.minimize,
        )
        self.make_topbar_button(
            trash_icon, trash_icon_hovered, "nw", 0, self.trash_image
        )
        self.rename_button_id: int = self.make_topbar_button(
            rename_icon, rename_icon_hovered, "nw", 0, self.toggle_show_rename_window
        )

        # details dropdown
        self.dropdown_button_id: int = self.canvas.create_image(
            screen_width - topbar_height - topbar_height,
            0,
            image=self.dropdown_hidden_icon,
            anchor="ne",
            tag="topbar",
            state="hidden",
        )
        self.canvas.tag_bind(
            self.dropdown_button_id, "<ButtonRelease-1>", self.toggle_details_dropdown
        )
        self.canvas.tag_bind(
            self.dropdown_button_id, "<Enter>", self.hover_dropdown_toggle
        )
        self.canvas.tag_bind(
            self.dropdown_button_id, "<Leave>", self.leave_hover_dropdown_toggle
        )
        self.dropdown_id: int = self.canvas.create_image(
            screen_width, topbar_height, anchor="ne", tag="topbar", state="hidden"
        )

        self.rename_window_id: int = self.canvas.create_window(
            0, 0, width=200, height=24, anchor="nw"
        )
        self.rename_entry: Entry = Entry(
            self.app, font=FONT, bg="#FEFEFE", borderwidth=0
        )
        self.rename_entry.bind("<Return>", self.try_rename_or_convert)
        self.rename_entry.bind("<KeyPress>", self.handle_keybinds_default)
        self.canvas.itemconfig(
            self.rename_window_id, state="hidden", window=self.rename_entry
        )

    # for simple buttons on topbar that only change on hover and have on click event
    def make_topbar_button(
        self,
        regular_image: PhotoImage,
        hovered_image: PhotoImage,
        anchor: str,
        x_offset: int,
        function_to_bind,
    ) -> int:
        button_id: int = self.canvas.create_image(
            x_offset,
            0,
            image=regular_image,
            anchor=anchor,
            tag="topbar",
            state="hidden",
        )

        self.canvas.tag_bind(
            button_id,
            "<Enter>",
            lambda _: self.canvas.itemconfig(button_id, image=hovered_image),
        )
        self.canvas.tag_bind(
            button_id,
            "<Leave>",
            lambda _: self.canvas.itemconfig(button_id, image=regular_image),
        )
        self.canvas.tag_bind(button_id, "<ButtonRelease-1>", function_to_bind)
        return button_id

    # wrapper for exit function to close rename window first if its open
    def escape_button(self, event: Optional[Event] = None) -> None:
        if self.canvas.itemcget(self.rename_window_id, "state") == "normal":
            self.hide_rename_window()
            return
        self.exit()

    # properly exit program
    def exit(self, event: Optional[Event] = None) -> None:
        self.image_loader.reset()
        self.canvas.delete(self.file_name_text_id)
        self.app.quit()
        self.app.destroy()
        exit(0)

    def leave_hover_dropdown_toggle(self, event: Optional[Event] = None) -> None:
        self.canvas.itemconfig(
            self.dropdown_button_id,
            image=self.dropdown_showing_icon
            if self.dropdown_shown
            else self.dropdown_hidden_icon,
        )

    def hover_dropdown_toggle(self, event: Optional[Event] = None) -> None:
        self.canvas.itemconfig(
            self.dropdown_button_id,
            image=self.dropdown_showing_icon_hovered
            if self.dropdown_shown
            else self.dropdown_hidden_icon_hovered,
        )

    def trash_image(self, event: Optional[Event] = None) -> None:
        self.clear_animation_variables()
        self.hide_rename_window()
        self.remove_image_and_move_to_next(delete_from_disk=True)

    def toggle_show_rename_window(self, event: Optional[Event] = None) -> None:
        if self.canvas.itemcget(self.rename_window_id, "state") == "normal":
            self.hide_rename_window()
            return

        if self.canvas.itemcget("topbar", "state") == "hidden":
            self.show_topbar()
        self.canvas.itemconfig(self.rename_window_id, state="normal")
        self.canvas.coords(self.rename_window_id, self.rename_window_x_offset + 40, 4)
        self.rename_entry.focus()

    def _ask_delete_after_convert(self, new_format: str) -> None:
        """Used as callback function for after a succecssful file conversion"""
        if askyesno(
            "Confirm deletion",
            f"Converted file to {new_format}, delete old file?",
        ):
            self.remove_image_and_move_to_next(delete_from_disk=True)

    def try_rename_or_convert(self, event: Optional[Event] = None) -> None:
        """Handles user input into rename window.
        Trys to convert or rename based on input"""
        try:
            self.file_manager.rename_or_convert_current_image(
                self.rename_entry.get().strip(),
                self._ask_delete_after_convert,
            )
        except Exception:
            # flash red to tell user rename failed
            self.rename_entry.config(bg="#e6505f")
            self.app.after(400, self.reset_entry_color)
            return

        # Cleanup after successful rename
        self.hide_rename_window()
        self.load_image()
        self.refresh_topbar()

    def reset_entry_color(self) -> None:
        self.rename_entry.config(bg="white")

    def minimize(self, event: Event) -> None:
        """Minimizes the app and sets flag to redraw current image when opened again"""
        self.redraw_screen = True
        self.app.iconify()

    def load_image(self) -> None:
        """Loads an image, resizes it to fit on the screen and updates display"""
        self.clear_animation_variables()

        # When load fails, keep removing bad image and trying to load next
        while (current_image := self.image_loader.load_image()) is None:
            self.remove_image(delete_from_disk=False)

        self.canvas.itemconfig(self.image_display_id, image=current_image)
        self.app.title(self.file_manager.current_image.name)

    def show_topbar(self, event: Optional[Event] = None) -> None:
        self.topbar_shown = True
        self.canvas.itemconfig("topbar", state="normal")
        self.refresh_topbar()

    def hide_topbar(self, event: Optional[Event] = None) -> None:
        self.app.focus()
        self.topbar_shown = False
        self.canvas.itemconfig("topbar", state="hidden")
        self.hide_rename_window()

    def handle_click(self, event: Event) -> None:
        self.hide_topbar() if self.topbar_shown else self.show_topbar()

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
        self.canvas.itemconfig(
            self.file_name_text_id, text=self.file_manager.current_image.name
        )
        self.rename_window_x_offset = self.canvas.bbox(self.file_name_text_id)[2]
        self.canvas.coords(self.rename_button_id, self.rename_window_x_offset, 0)
        (
            self.create_details_dropdown()
            if self.dropdown_shown
            else self.canvas.itemconfig(self.dropdown_id, state="hidden")
        )

    def animation_loop(self, ms_until_next_frame: int, ms_backoff: int) -> None:
        self.animation_id = self.app.after(
            ms_until_next_frame, self.animate, ms_backoff
        )

    def animate(self, ms_backoff: int) -> None:
        """
        displays a frame on screen and recursively calls itself after a delay
        frame_index: index of current frame to be displayed
        speed: speed in ms until next frame
        """
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

    # cleans up after an animated file was opened
    def clear_animation_variables(self) -> None:
        if self.animation_id == "":
            return

        self.app.after_cancel(self.animation_id)
        self.animation_id = ""
        self.image_loader.reset()

    def toggle_details_dropdown(self, event: Optional[Event] = None) -> None:
        self.dropdown_shown = not self.dropdown_shown
        self.hover_dropdown_toggle()  # fake mouse hover
        (
            self.create_details_dropdown()
            if self.dropdown_shown
            else self.canvas.itemconfig(self.dropdown_id, state="hidden")
        )

    def create_details_dropdown(self) -> None:
        image_info: CachedImageData = self.file_manager.get_current_image_cache()
        dimension_text: str = f"Pixels: {image_info.width}x{image_info.height}"
        size_text: str = f"Size: {image_info.dimensions}"

        self.dropdown_image = create_dropdown_image(dimension_text, size_text)
        self.canvas.itemconfig(
            self.dropdown_id, image=self.dropdown_image, state="normal"
        )


# For testing
if __name__ == "__main__":
    ViewerApp(r"c:\photos\test.jpg", "C:/Python/Viewer")
