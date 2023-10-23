from tkinter import Canvas, Tk

from PIL.ImageTk import PhotoImage


# responsible for displaying images to screen and animation loop
class DisplayManager:
    DEFAULT_GIF_SPEED: int = 100
    ANIMATION_SPEED_FACTOR: float = 0.75

    __slots__ = (
        "app",
        "canvas",
        "image_display_id",
        "aniamtion_frames",
        "animation_id",
    )

    def __init__(self, app: Tk, canvas: Canvas, image_display_id: int) -> None:
        self.app = app
        self.canvas = canvas
        self.image_display_id = image_display_id

        self.aniamtion_frames: list = []
        self.animation_id: str = ""

    def update_image(self, new_image: PhotoImage) -> None:
        self.canvas.itemconfig(self.image_display_id, image=new_image)

    def start_animate(
        self,
        first_frame: PhotoImage,
        frame_count: int,
        duration: int,
    ) -> None:
        self.aniamtion_frames = [None] * frame_count
        self.aniamtion_frames[0] = first_frame

        try:
            speed = int(duration * self.ANIMATION_SPEED_FACTOR)
            if speed < 2:
                speed = self.DEFAULT_GIF_SPEED
        except (KeyError, AttributeError):
            speed = self.DEFAULT_GIF_SPEED

        self.animation_id = self.app.after(speed + 20, self.animate_frame, 1, speed)

    def animate_frame(self, frame_index: int, speed: int) -> None:
        """
        displays a frame on screen and recursively calls itself after a delay
        frame_index: index of current frame to be displayed
        speed: speed in ms until next frame
        """
        frame_index += 1
        if frame_index >= len(self.aniamtion_frames):
            frame_index = 0

        ms_until_next_frame: int = speed
        current_frame: PhotoImage = self.aniamtion_frames[frame_index]
        # if tried to show next frame before it is loaded
        # reset to current frame and try again after delay
        if current_frame is None:
            frame_index -= 1
            ms_until_next_frame += 10
        else:
            self.update_image(current_frame)

        self.animation_id = self.app.after(
            ms_until_next_frame, self.animate_frame, frame_index, speed
        )

    def end_animation(self) -> None:
        self.app.after_cancel(self.animation_id)
        self.animation_id = ""
        self.aniamtion_frames.clear()

    def is_animating(self) -> bool:
        return self.animation_id != ""
