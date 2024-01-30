from tkinter import Canvas

from PIL.ImageTk import PhotoImage


class CustomCanvas(Canvas):
    """Custom version of tkinter's canvas to support internal methods"""

    __slots__ = (
        "image_display_id",
        "move_x",
        "move_y",
        "screen_width",
        "screen_height",
        "topbar",
    )

    def __init__(self, master) -> None:
        super().__init__(master, bg="black", highlightthickness=0)
        self.pack(anchor="nw", fill="both", expand=1)

        self.move_x: int = 0
        self.move_y: int = 0

    def finish_init(self, screen_width: int, screen_height: int) -> None:
        """Finishes init since screen size not known before canvas needs to display"""
        self.create_rectangle(
            0, 0, screen_width, screen_height, fill="black", tag="back"
        )
        self.image_display_id = self.create_image(
            screen_width >> 1, screen_height >> 1, anchor="center", tag="back"
        )
        self.screen_width = screen_width
        self.screen_height = screen_height

    def create_topbar(self, topbar_img: PhotoImage) -> None:
        """Creates the topbar and stores it"""
        self.topbar = topbar_img  # need to do this so garbage collector doesn't kill it
        self.create_image(
            0, 0, image=topbar_img, anchor="nw", tag="topbar", state="hidden"
        )

    def update_img_display(self, new_image: PhotoImage) -> None:
        """Updates dispalyed with a new image"""
        self.itemconfigure(self.image_display_id, image=new_image)

    def update_img_display_and_location(self, new_image: PhotoImage) -> None:
        """Updates dispalyed with a new image and internal location metric"""
        self.move(self.image_display_id, self.move_x, self.move_y)
        self.update_img_display(new_image)
        self.move_x = 0
        self.move_y = 0

    def handle_ctrl_arrow_keys(self, keycode: int) -> None:
        """Move onscreen image when ctrl+arrow key clicked/held"""
        bbox: tuple = self.bbox(self.image_display_id)
        match keycode:
            case 37:  # Left
                x = -10
                y = 0
                if (not bbox[2] > self.screen_width) and (bbox[0] + x) < 0:
                    return
            case 38:  # Up
                x = 0
                y = -10
                if (bbox[1] + y) < 0 and (not bbox[3] > self.screen_height):
                    return
            case 39:  # Right
                x = 10
                y = 0
                if (bbox[2] + x) > self.screen_width and (not bbox[0] < 0):
                    return
            case _:  # Down
                x = 0
                y = 10
                if (bbox[3] + y) > self.screen_height and (not bbox[1] < 0):
                    return
        self.move_x -= x
        self.move_y -= y

        # TODO: find a good way to handle scaling 10px to screen, don't
        # really want to call the internal scale function each time...
        self.move(self.image_display_id, x, y)
