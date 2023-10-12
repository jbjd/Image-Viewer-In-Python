from sys import argv
from tkinter import Tk, Canvas, Entry, Event
from tkinter.messagebox import askyesno
from threading import Thread
import os

from factories.icon_factory import IconFactory
from managers.file_manager import ImageFileManager

from PIL import Image, ImageTk, ImageDraw, ImageFont, UnidentifiedImageError
import cv2
from numpy import asarray
from turbojpeg import TurboJPEG, TJPF_RGB


class Viewer:
    DEFAULT_GIF_SPEED: int = 100
    ANIMATION_SPEED_FACTOR: float = 0.75

    __slots__ = (
        "size_ratio",
        "jpeg_helper",
        "topbar_shown",
        "dropdown_shown",
        "redraw_screen",
        "dropdown_image",
        "rename_window_x_offset",
        "image_size",
        "aniamtion_frames",
        "animation_id",
        "app",
        "canvas",
        "screen_w",
        "screen_h",
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
        "image_height",
        "image_width",
        "current_image",
        "dropdown_button_id",
        "rename_button_id",
        "KEY_MAPPING",
        "KEY_MAPPING_LIMITED",
    )

    def __init__(self, first_image_to_show: str) -> None:
        self.file_manager = ImageFileManager(first_image_to_show)

        # UI varaibles
        self.topbar_shown: bool = False
        self.dropdown_shown: bool = False
        self.redraw_screen: bool = False

        # data on current image
        self.image_width: int = 0
        self.image_height: int = 0
        self.rename_window_x_offset: int = 0
        self.image_size: str = ""

        # variables used for animations, empty when no animation playing
        self.aniamtion_frames: list = []
        self.animation_id: str = ""

        # helpers for specific file types
        path_to_exe = os.path.dirname(os.path.realpath(argv[0]))
        self.jpeg_helper = TurboJPEG(f"{path_to_exe}/util/libturbojpeg.dll")

        # application and canvas
        self.app: Tk = Tk()
        if os.name == "nt":
            self.app.iconbitmap(default=f"{path_to_exe}/icon/icon.ico")

        self.canvas: Canvas = Canvas(self.app, bg="black", highlightthickness=0)
        self.canvas.pack(anchor="nw", fill="both", expand=1)
        self.app.attributes("-fullscreen", True)
        self.app.state("zoomed")
        self.app.update()  # updates winfo width and height to the current size
        self.screen_w: int = self.app.winfo_width()
        self.screen_h: int = self.app.winfo_height()
        self.size_ratio: float = self.screen_h / 1080
        background = self.canvas.create_rectangle(
            0, 0, self.screen_w, self.screen_h, fill="black"
        )
        self.image_display_id = self.canvas.create_image(
            self.screen_w >> 1, self.screen_h >> 1, anchor="center"
        )
        self.load_assests(self.scale_pixels_to_screen(32))

        # draw first image, then get all image paths in directory
        self.image_loader()
        self.app.update()
        self.file_manager.fully_load_images()
        ImageDraw.ImageDraw.font = ImageFont.truetype(
            "arial.ttf", self.scale_pixels_to_screen(22)
        )
        ImageDraw.ImageDraw.fontmode = "L"  # antialiasing

        # events based on input
        self.KEY_MAPPING = {
            "r": self.toggle_show_rename_window,
            "Left": self.arrow,
            "Right": self.arrow,
        }  # allowed only in main app
        self.KEY_MAPPING_LIMITED = {
            "F2": self.toggle_show_rename_window,
            "Up": self.hide_topbar,
            "Down": self.show_topbar,
        }  # allowed in entry or main app
        self.canvas.tag_bind(background, "<Button-1>", self.handle_click)
        self.canvas.tag_bind(self.image_display_id, "<Button-1>", self.handle_click)
        self.app.bind("<FocusIn>", self.redraw)
        self.app.bind("<MouseWheel>", self.scroll)
        self.app.bind("<Escape>", self.escape_button)
        self.app.bind("<KeyRelease>", self.handle_all_keybinds)

        self.app.mainloop()

    def scale_pixels_to_screen(self, original_pixels: int) -> int:
        """Normalize all pixels relative to a 1080 pixel tall screen"""
        return int(original_pixels * self.size_ratio)

    def handle_all_keybinds(self, event: Event) -> None:
        if event.widget is self.app:
            if event.keysym in self.KEY_MAPPING:
                self.KEY_MAPPING[event.keysym](event)
            else:
                self.handle_limited_keybinds(event)

    def handle_limited_keybinds(self, event: Event) -> None:
        if event.keysym in self.KEY_MAPPING_LIMITED:
            self.KEY_MAPPING_LIMITED[event.keysym](event)

    def arrow(self, event: Event) -> None:
        # only move images if user not in entry
        if event.widget is self.app:
            self.move(1 if event.keysym == "Right" else -1)

    def scroll(self, event: Event) -> None:
        self.move(-1 if event.delta > 0 else 1)

    def hide_rename_window(self) -> None:
        self.canvas.itemconfig(self.rename_window_id, state="hidden")
        self.app.focus()

    def move(self, amount: int) -> None:
        """
        Move to different image
        amount: 1 or -1 indicating movement to next or previous
        """
        self.hide_rename_window()
        self.file_manager.move_current_index(amount)

        self.image_loader_safe()
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
        self.image_loader_safe()

    def load_assests(self, topbar_height) -> None:
        """
        Load all assets on topbar from factory and create tkinter objects
        topbar_height: size to make icons/topbar
        """
        FONT: str = "arial 11"

        icon_factory = IconFactory(topbar_height, self.screen_w)
        self.topbar = icon_factory.make_topbar()

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
            36,
            5,
            text="",
            fill="white",
            anchor="nw",
            font=FONT,
            tag="topbar",
            state="hidden",
        )
        self.make_topbar_button(
            exit_icon, exit_icon_hovered, "ne", self.screen_w, self.exit
        )
        self.make_topbar_button(
            minify_icon,
            minify_icon_hovered,
            "ne",
            self.screen_w - topbar_height,
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
            self.screen_w - topbar_height - topbar_height,
            0,
            image=self.dropdown_hidden_icon,
            anchor="ne",
            tag="topbar",
            state="hidden",
        )
        self.canvas.tag_bind(
            self.dropdown_button_id, "<Button-1>", self.toggle_details_dropdown
        )
        self.canvas.tag_bind(
            self.dropdown_button_id, "<Enter>", self.hover_dropdown_toggle
        )
        self.canvas.tag_bind(
            self.dropdown_button_id, "<Leave>", self.leave_hover_dropdown_toggle
        )
        self.dropdown_id: int = self.canvas.create_image(
            self.screen_w, topbar_height, anchor="ne", tag="topbar", state="hidden"
        )

        self.rename_window_id: int = self.canvas.create_window(
            0, 0, width=200, height=24, anchor="nw"
        )
        self.rename_entry: Entry = Entry(self.app, font=FONT)
        self.rename_entry.bind("<Return>", self.try_rename_or_convert)
        self.rename_entry.bind("<KeyRelease>", self.handle_limited_keybinds)
        self.canvas.itemconfig(
            self.rename_window_id, state="hidden", window=self.rename_entry
        )

    # for simple buttons on topbar that only change on hover and have on click event
    def make_topbar_button(
        self,
        regular_image: ImageTk.PhotoImage,
        hovered_image: ImageTk.PhotoImage,
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
        self.canvas.tag_bind(button_id, "<Button-1>", function_to_bind)
        return button_id

    # wrapper for exit function to close rename window first if its open
    def escape_button(self, event: Event = None) -> None:
        if self.canvas.itemcget(self.rename_window_id, "state") == "normal":
            self.hide_rename_window()
            return
        self.exit()

    # properly exit program
    def exit(self, event: Event = None) -> None:
        self.canvas.delete(self.file_name_text_id)
        self.app.quit()
        self.app.destroy()
        exit(0)

    def leave_hover_dropdown_toggle(self, event: Event = None) -> None:
        self.canvas.itemconfig(
            self.dropdown_button_id,
            image=self.dropdown_showing_icon
            if self.dropdown_shown
            else self.dropdown_hidden_icon,
        )

    def hover_dropdown_toggle(self, event: Event = None) -> None:
        self.canvas.itemconfig(
            self.dropdown_button_id,
            image=self.dropdown_showing_icon_hovered
            if self.dropdown_shown
            else self.dropdown_hidden_icon_hovered,
        )

    def trash_image(self, event: Event = None) -> None:
        self.clear_animation_variables()
        self.hide_rename_window()
        self.remove_image_and_move_to_next(delete_from_disk=True)

    def toggle_show_rename_window(self, event: Event = None) -> None:
        if self.canvas.itemcget(self.rename_window_id, "state") == "normal":
            self.hide_rename_window()
            return

        if self.canvas.itemcget("topbar", "state") == "hidden":
            self.show_topbar()
        self.canvas.itemconfig(self.rename_window_id, state="normal")
        self.canvas.coords(self.rename_window_id, self.rename_window_x_offset + 40, 4)
        self.rename_entry.focus()

    def cleanup_after_rename(self) -> None:
        self.hide_rename_window()
        self.image_loader_safe()
        self.refresh_topbar()

    def try_rename_or_convert(self, event: Event = None) -> None:
        try:
            was_converted = self.file_manager.rename_or_convert_current_image(
                self.temp, self.rename_entry.get().strip()
            )
        except Exception:
            # flash red to tell user rename failed
            self.rename_entry.config(bg="#e6505f")
            self.app.after(400, self.reset_entry_color)
            return

        if was_converted and askyesno(
            "Confirm deletion",
            "Converted file to new format, delete old file?",
        ):
            self.remove_image_and_move_to_next(delete_from_disk=True)

        self.cleanup_after_rename()

    def reset_entry_color(self):
        self.rename_entry.config(bg="white")

    def minimize(self, event: Event) -> None:
        self.redraw_screen = True
        self.app.iconify()

    def get_jpeg_scale_factor(self) -> tuple[int, int] | None:
        """Gets scaling factor for images larger than screen"""
        ratio_to_screen: float = self.image_height / self.screen_h
        if ratio_to_screen >= 4:
            return (1, 4)
        if ratio_to_screen >= 2:
            return (1, 2)
        return None

    def get_image_fit_to_screen(
        self, interpolation: int, dimensions: tuple[int, int]
    ) -> ImageTk.PhotoImage:
        # faster way of decoding to numpy array for JPEG
        if self.temp.format == "JPEG":
            with open(self.file_manager.path_to_current_image, "rb") as im_bytes:
                image_as_array = self.jpeg_helper.decode(
                    im_bytes.read(), TJPF_RGB, self.get_jpeg_scale_factor(), 0
                )
        else:
            # cv2 resize is faster than PIL, but convert to RGB then resize is slower
            # PIL resize for non-RGB(A) mode images looks very bad so still use cv2
            image_as_array = asarray(
                self.temp if self.temp.mode != "P" else self.temp.convert("RGB"),
                order="C",
            )
        return ImageTk.PhotoImage(
            Image.fromarray(
                cv2.resize(image_as_array, dimensions, interpolation=interpolation)
            )
        )

    def dimension_finder(self) -> tuple[int, int]:
        width: int = round(self.image_width * (self.screen_h / self.image_height))

        # fit to height if width in screen,
        # else fit to width and let height go off screen
        return (
            (width, self.screen_h)
            if width <= self.screen_w
            else (
                self.screen_w,
                round(self.image_height * (self.screen_w / self.image_width)),
            )
        )

    # loads and displays an image
    def image_loader(self) -> None:
        current_image_data = self.file_manager.current_image

        try:
            # open even if in cache to throw error if user deleted it outside of program
            self.temp = Image.open(self.file_manager.path_to_current_image)
        except (FileNotFoundError, UnidentifiedImageError) as e:
            print(e)
            self.remove_image_and_move_to_next(delete_from_disk=False)
            return

        bit_size: int = os.path.getsize(self.file_manager.path_to_current_image)

        # check if was cached and not changed outside of program
        cached_img_data = self.file_manager.cache.get(current_image_data.name, None)
        if cached_img_data is not None and bit_size == cached_img_data.bit_size:
            self.image_width = cached_img_data.width
            self.image_height = cached_img_data.height
            self.image_size = cached_img_data.size_as_text
            self.current_image = cached_img_data.image
            self.temp.close()
        else:
            self.image_width, self.image_height = self.temp.size
            size_kb: int = bit_size >> 10
            self.image_size = (
                f"{round(size_kb/10.24)/100}mb" if size_kb > 999 else f"{size_kb}kb"
            )
            dimensions = self.dimension_finder()
            frame_count: int = getattr(self.temp, "n_frames", 1)
            interpolation: int = (
                cv2.INTER_AREA if self.image_height > self.screen_h else cv2.INTER_CUBIC
            )
            self.current_image = self.get_image_fit_to_screen(interpolation, dimensions)

            # special case, file is animated
            if frame_count > 1:
                self.aniamtion_frames = [None] * frame_count
                self.aniamtion_frames[0] = self.current_image
                Thread(
                    target=self.load_frame,
                    args=(1, dimensions, current_image_data.name, interpolation),
                    daemon=True,
                ).start()
                # find animation frame speed
                try:
                    speed = int(
                        self.temp.info["duration"] * self.ANIMATION_SPEED_FACTOR
                    )
                    if speed < 2:
                        speed = self.DEFAULT_GIF_SPEED
                except (KeyError, AttributeError):
                    speed = self.DEFAULT_GIF_SPEED

                self.animation_id = self.app.after(speed + 20, self.animate, 1, speed)
            else:
                # cache non-animated images
                self.file_manager.cache_current_image(
                    self.image_width,
                    self.image_height,
                    self.image_size,
                    self.current_image,
                    bit_size,
                )
                self.temp.close()
        self.canvas.itemconfig(self.image_display_id, image=self.current_image)
        self.app.title(current_image_data.name)

    def image_loader_safe(self) -> None:
        """Wrapper for image_loader when an animation might have been playing"""
        self.clear_animation_variables()
        self.image_loader()

    def show_topbar(self, event: Event = None) -> None:
        self.topbar_shown = True
        self.canvas.itemconfig("topbar", state="normal")
        self.refresh_topbar()

    def hide_topbar(self, event: Event = None) -> None:
        self.app.focus()
        self.topbar_shown = False
        self.canvas.itemconfig("topbar", state="hidden")
        self.hide_rename_window()

    def handle_click(self, event: Event) -> None:
        self.hide_topbar() if self.topbar_shown else self.show_topbar()

    def remove_image_and_move_to_next(self, delete_from_disk: bool) -> None:
        remaining_image_count: int = self.file_manager.remove_current_image(
            delete_from_disk
        )

        if remaining_image_count <= 0:
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

    # START ANIMATION FUNCTIONS
    def animate(self, frame_index: int, speed: int) -> None:
        """
        displays a frame on screen and recursively calls itself after a delay
        frame_index: index of current frame to be displayed
        speed: speed in ms until next frame
        """
        frame_index += 1
        if frame_index >= len(self.aniamtion_frames):
            frame_index = 0

        ms_until_next_frame: int = speed
        current_frame: ImageTk.PhotoImage = self.aniamtion_frames[frame_index]
        # if tried to show next frame before it is loaded
        # reset to current frame and try again after delay
        if current_frame is None:
            frame_index -= 1
            ms_until_next_frame += 10
        else:
            self.canvas.itemconfig(self.image_display_id, image=current_frame)

        self.animation_id = self.app.after(
            ms_until_next_frame, self.animate, frame_index, speed
        )

    def load_frame(
        self,
        frame_index: int,
        dimensions: tuple[int, int],
        file_name: str,
        interpolation: int,
    ) -> None:
        # if user moved to new image, don't keep loading previous animated image
        if file_name != self.file_manager.current_image.name:
            return
        try:
            self.temp.seek(frame_index)
            self.aniamtion_frames[frame_index] = self.get_frame_fit_to_screen(
                interpolation, dimensions
            )
            self.load_frame(frame_index + 1, dimensions, file_name, interpolation)
        except Exception:
            # Scrolling, recursion ending, etc cause variety of errors
            # Catch and close if thread was for current animation
            if file_name == self.file_manager.current_image.name:
                self.temp.close()

    def get_frame_fit_to_screen(
        self, interpolation: int, dimensions: tuple[int, int]
    ) -> ImageTk.PhotoImage:
        return ImageTk.PhotoImage(
            Image.fromarray(
                cv2.resize(
                    asarray(self.temp.convert("RGB"), order="C"),
                    dimensions,
                    interpolation=interpolation,
                )
            )
        )

    # cleans up after an animated file was opened
    def clear_animation_variables(self) -> None:
        if self.animation_id == "":
            return

        self.app.after_cancel(self.animation_id)
        self.animation_id = ""
        self.aniamtion_frames.clear()
        self.temp.close()

    # END ANIMATION FUNCTIONS

    # START DROPDOWN FUNCTIONS
    def toggle_details_dropdown(self, event: Event) -> None:
        self.dropdown_shown = not self.dropdown_shown
        self.hover_dropdown_toggle()  # fake mouse hover
        (
            self.create_details_dropdown()
            if self.dropdown_shown
            else self.canvas.itemconfig(self.dropdown_id, state="hidden")
        )

    def create_details_dropdown(self) -> None:
        image_dimension_text: str = f"Pixels: {self.image_width}x{self.image_height}"

        text_bbox: tuple = ImageDraw.ImageDraw.font.getbbox(image_dimension_text)

        box_to_draw_on = ImageDraw.Draw(
            Image.new(
                "RGBA", (text_bbox[2] + 20, text_bbox[3] * 5 + 10), (40, 40, 40, 170)
            ),
            "RGBA",
        )
        box_to_draw_on.text((10, text_bbox[3] + 5), image_dimension_text, fill="white")
        box_to_draw_on.text(
            (10, int(text_bbox[3] * 3)), f"Size: {self.image_size}", fill="white"
        )

        self.dropdown_image = ImageTk.PhotoImage(box_to_draw_on._image)
        self.canvas.itemconfig(
            self.dropdown_id, image=self.dropdown_image, state="normal"
        )

    # END DROPDOWN FUNCTIONS


# For testing
if __name__ == "__main__":
    Viewer(r"c:\Users\jimde\OneDrive\Pictures\test.jpg")
