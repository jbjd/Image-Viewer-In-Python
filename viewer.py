from typing import Optional
from collections.abc import Callable
import os
from threading import Thread
from tkinter import Canvas, Entry, Event, Tk
from tkinter.messagebox import askyesno

from PIL.Image import Image, open as open_image
from PIL import UnidentifiedImageError
from PIL.ImageTk import PhotoImage

from factories.icon_factory import IconFactory
from helpers.image_resize import ImageResizeHelper
from image import (
    CachedInfo,
    CachedInfoAndImage,
    ImagePath,
    create_dropdown_image,
    init_font,
)
from managers.file_manager import ImageFileManager


class Viewer:
    DEFAULT_GIF_SPEED: int = 100
    ANIMATION_SPEED_FACTOR: float = 0.75

    __slots__ = (
        "size_ratio",
        "image_resizer",
        "topbar_shown",
        "dropdown_shown",
        "redraw_screen",
        "dropdown_image",
        "rename_window_x_offset",
        "aniamtion_frames",
        "animation_id",
        "app",
        "canvas",
        "image_display_id",
        "file_manager",
        "topbar",
        "file_name_text_id",
        "dropdown_hidden_icon",
        "dropdown_hidden_icon_hovered",
        "dropdown_showing_icon",
        "dropdown_showing_icon_hovered",
        "rename_window_id",
        "dropdown_id",
        "rename_entry",
        "temp",
        "dropdown_button_id",
        "rename_button_id",
        "key_bindings",
        "move_id",
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

        # variables used for animations, empty when no animation playing
        self.aniamtion_frames: list = []
        self.animation_id: str = ""

        # application and canvas
        self.app = Tk()
        if os.name == "nt":
            self.app.iconbitmap(default=os.path.join(path_to_exe, "icon/icon.ico"))

        self.canvas = Canvas(self.app, bg="black", highlightthickness=0)
        self.canvas.pack(anchor="nw", fill="both", expand=1)
        self.app.attributes("-fullscreen", True)
        self.app.state("zoomed")
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

        # move this to file_manager later
        self.image_resizer = ImageResizeHelper(screen_width, screen_height, path_to_exe)

        # draw first image, then get all image paths in directory
        self.image_loader()
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
        self.app.bind("<MouseWheel>", self.scroll)
        self.app.bind("<Escape>", self.escape_button)
        self.app.bind("<KeyPress>", self.handle_keybinds_main)
        self.app.bind("<KeyRelease>", self.handle_key_release)

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

    def scroll(self, event: Event) -> None:
        self.move(-1 if event.delta > 0 else 1)

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

        self.image_loader()
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
        self.image_loader()

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
        self.rename_entry: Entry = Entry(self.app, font=FONT)
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
        self.temp.close()
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
        self.image_loader()
        self.refresh_topbar()

    def reset_entry_color(self) -> None:
        self.rename_entry.config(bg="white")

    def minimize(self, event: Event) -> None:
        """Minimizes the app and sets flag to redraw current image when opened again"""
        self.redraw_screen = True
        self.app.iconify()

    # loads and displays an image
    def image_loader(self) -> None:
        self.clear_animation_variables()
        current_image_data: ImagePath = self.file_manager.current_image

        try:
            # open even if in cache to throw error if user deleted it outside of program
            self.temp = open_image(self.file_manager.path_to_current_image)
        except (FileNotFoundError, UnidentifiedImageError):
            self.remove_image_and_move_to_next(delete_from_disk=False)
            return

        bit_size: int = os.stat(self.file_manager.path_to_current_image).st_size

        # check if was cached and not changed outside of program
        cached_img_data = self.file_manager.cache.get(current_image_data.name, False)
        if (
            cached_img_data
            and isinstance(cached_img_data, CachedInfoAndImage)
            and bit_size == cached_img_data.bit_size
        ):
            current_image = cached_img_data.image
            self.temp.close()
        else:
            image_width, image_height = self.temp.size
            size_kb: int = bit_size >> 10
            image_size = (
                f"{round(size_kb/10.24)/100}mb" if size_kb > 999 else f"{size_kb}kb"
            )

            frame_count: int = getattr(self.temp, "n_frames", 1)
            if self.temp.format == "JPEG":
                current_image = self.image_resizer.get_jpeg_fit_to_screen(
                    self.temp, self.file_manager.path_to_current_image
                )
            else:
                current_image = self.image_resizer.get_image_fit_to_screen(self.temp)

            # special case, file is animated
            if frame_count > 1:
                self.aniamtion_frames = [None] * frame_count
                try:
                    speed = int(
                        self.temp.info["duration"] * self.ANIMATION_SPEED_FACTOR
                    )
                    if speed < 1:
                        speed = self.DEFAULT_GIF_SPEED
                except (KeyError, AttributeError):
                    speed = self.DEFAULT_GIF_SPEED

                self.aniamtion_frames[0] = current_image, speed
                Thread(
                    target=self.load_frame,
                    args=(self.temp, 1, frame_count),
                    daemon=True,
                ).start()
                # find animation frame speed

                self.animation_id = self.app.after(speed + 20, self.animate, 1, speed)
                self.file_manager.cache_info(
                    image_width,
                    image_height,
                    image_size,
                )
            else:
                # cache non-animated images
                self.file_manager.cache_image(
                    image_width,
                    image_height,
                    image_size,
                    current_image,
                    bit_size,
                )
                self.temp.close()
        self.canvas.itemconfig(self.image_display_id, image=current_image)
        self.app.title(current_image_data.name)

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

    def remove_image_and_move_to_next(self, delete_from_disk: bool) -> None:
        try:
            self.file_manager.remove_current_image(delete_from_disk)
        except IndexError:
            self.exit()

        self.image_loader()
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

    def animate(self, frame_index: int, speed: int) -> None:
        """
        displays a frame on screen and recursively calls itself after a delay
        frame_index: index of current frame to be displayed
        speed: speed in ms until next frame
        """
        frame_index += 1
        if frame_index >= len(self.aniamtion_frames):
            frame_index = 0

        frame_and_speed: tuple[PhotoImage, int] = self.aniamtion_frames[frame_index]
        # if tried to show next frame before it is loaded
        # reset to current frame and try again after delay
        if frame_and_speed is None:
            frame_index -= 1
            ms_until_next_frame = int(speed * 1.4)
        else:
            self.canvas.itemconfig(self.image_display_id, image=frame_and_speed[0])
            ms_until_next_frame = frame_and_speed[1]

        self.animation_id = self.app.after(
            ms_until_next_frame, self.animate, frame_index, speed
        )

    def load_frame(
        self,
        original_image: Image,
        frame_index: int,
        last_frame: int,
    ) -> None:
        # if user moved to new image, don't keep loading previous animated image
        if self.temp is not original_image:
            return
        try:
            self.temp.seek(frame_index)
            try:
                speed = int(self.temp.info["duration"] * self.ANIMATION_SPEED_FACTOR)
                if speed < 1:
                    speed = self.DEFAULT_GIF_SPEED
            except (KeyError, AttributeError):
                speed = self.DEFAULT_GIF_SPEED
            self.aniamtion_frames[frame_index] = (
                self.image_resizer.get_image_fit_to_screen(self.temp),
                speed,
            )
        except Exception:
            # changing images during load causes a variety of errors
            pass
        frame_index += 1
        if frame_index < last_frame:
            self.load_frame(original_image, frame_index, last_frame)
        elif self.temp is original_image:
            self.temp.close()

    # cleans up after an animated file was opened
    def clear_animation_variables(self) -> None:
        if self.animation_id == "":
            return

        self.app.after_cancel(self.animation_id)
        self.animation_id = ""
        self.aniamtion_frames.clear()
        self.temp.close()

    def toggle_details_dropdown(self, event: Optional[Event] = None) -> None:
        self.dropdown_shown = not self.dropdown_shown
        self.hover_dropdown_toggle()  # fake mouse hover
        (
            self.create_details_dropdown()
            if self.dropdown_shown
            else self.canvas.itemconfig(self.dropdown_id, state="hidden")
        )

    def create_details_dropdown(self) -> None:
        image_info: CachedInfo = self.file_manager.get_current_image_cache()
        dimension_text: str = f"Pixels: {image_info.width}x{image_info.height}"
        size_text: str = f"Size: {image_info.dimensions}"

        self.dropdown_image = create_dropdown_image(dimension_text, size_text)
        self.canvas.itemconfig(
            self.dropdown_id, image=self.dropdown_image, state="normal"
        )


# For testing
if __name__ == "__main__":
    Viewer(r"c:\photos\test.jpg", "C:/PythonCode/Viewer")
