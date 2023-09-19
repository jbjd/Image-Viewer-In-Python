# python -m nuitka --windows-disable-console --windows-icon-from-ico="C:\PythonCode\Viewer\icon\icon.ico" --mingw64 viewer.py
# std librarys
from sys import argv
from tkinter import Tk, Canvas, Entry, Event
from tkinter.messagebox import askyesno
from threading import Thread
import os
from re import sub
# non-std librarys
from PIL import Image, ImageTk, ImageDraw, ImageFont, UnidentifiedImageError  # 10.0.0
from send2trash import send2trash  # 1.8.2
import cv2  # 4.8.0.76
from numpy import asarray  # 1.25.2
import simplejpeg  # 1.7.2
import pyperclip  # 1.8.2

path_to_exe: str = argv[0].replace('\\', '/')
path_to_exe = path_to_exe[:path_to_exe.rfind('/')+1]
if os.name == "nt":
	from ctypes import windll

	class WinUtil():
		__slots__ = ()

		def my_cmp_w(self, a, b) -> bool:
			return windll.shlwapi.StrCmpLogicalW(a, b) < 0
	utilHelper = WinUtil()
else:
	# default functions, currently only support windows
	class DefaultUtil():
		__slots__ = ()

		def my_cmp_w(self, a, b) -> bool:
			if a == b:
				return 0
			return a < b
	utilHelper = DefaultUtil()


class Viewer:
	# class vars
	DEFAULT_SPEED: int = 100
	ANIMATION_SPEED_FACTOR: float = .75
	VALID_FILE_TYPES: set[str] = {".png", ".jpg", ".jpeg", ".jfif", ".jif", ".jpe", ".webp", ".gif", ".bmp"}

	# struct for holding cached images, for some reason this stores less data than a regular tuple based on my tests
	class CachedImage:
		__slots__ = ("width", "height", "size_as_text", "image", "bit_size")

		def __init__(self, width, height, size_as_text, image, bit_size) -> None:
			self.width: int = width
			self.height: int = height
			self.size_as_text: str = size_as_text
			self.image: ImageTk.PhotoImage = image
			self.bit_size: int = bit_size

	class ImagePath():
		__slots__ = ("suffix", "name")

		def __init__(self, name: str) -> None:
			self.suffix = name[name.rfind('.'):].lower()
			self.name = name

	# key for sorting
	class IKey:
		__slots__ = ("name")

		def __init__(self, image: str) -> None:
			self.name: str = image.name

		def __lt__(self, b) -> bool:
			return utilHelper.my_cmp_w(self.name, b.name)

	__slots__ = ("OS_illegal_chars", "full_path", "image_directory", "topbar_shown", "dropdown_shown", "redraw_screen", "dropdown_image", "trueWidth", "trueHeigh", "rename_window_x_offset", "bit_size", "trueSize", "aniamtion_frames", "animation_id", "app", "cache", "canvas", "screen_w", "screen_h", "image_display", "files", "cur_index", "topbar", "dropbar", "file_name_display_text", "dropb", "hoverDrop", "upb", "hoverUp", "inp", "infod", "rename_entry", "temp", "trueHeight", "trueWidth", "conImg", "dbox", "rename_button", "KEY_MAPPING", "KEY_MAPPING_LIMITED")

	def __init__(self, image_path_raw: str) -> None:
		image_path_raw = image_path_raw.replace('\\', '/')
		if not os.path.isfile(image_path_raw) or image_path_raw[image_path_raw.rfind('.'):] not in self.VALID_FILE_TYPES:
			exit(1)

		self.image_directory: str = image_path_raw[:image_path_raw.rfind('/')+1]
		if not os.access(self.image_directory, os.W_OK):
			exit(1)

		# UI varaibles
		self.topbar_shown: bool = False
		self.dropdown_shown: bool = False
		self.redraw_screen: bool = False

		# data on current image
		self.trueWidth: int = 0
		self.trueHeigh: int = 0
		self.rename_window_x_offset: int = 0
		self.bit_size: int = 0
		self.cur_index: int = 0
		self.trueSize: str = ""

		# variables used for animations, empty when no animation playing
		self.aniamtion_frames: list = []
		self.animation_id: str = ""

		# application and canvas
		self.app: Tk = Tk()
		if os.name == 'nt':
			self.app.iconbitmap(default=f"{path_to_exe}icon/icon.ico")
			self.OS_illegal_chars: str = '[\\\\/<>:"|?*]'
		else:
			self.OS_illegal_chars: str = '[/]'

		self.cache: dict[str, self.CachedImage] = {}
		self.canvas: Canvas = Canvas(self.app, bg="black", highlightthickness=0)
		self.canvas.pack(anchor="nw", fill="both", expand=1)
		self.app.attributes("-fullscreen", True)
		self.app.state("zoomed")
		self.app.update()  # updates winfo width and height to the current size, this is necessary
		self.screen_w: int = self.app.winfo_width()
		self.screen_h: int = self.app.winfo_height()
		background = self.canvas.create_rectangle(0, 0, self.screen_w, self.screen_h, fill="black")
		self.image_display = self.canvas.create_image(self.screen_w >> 1, self.screen_h >> 1, anchor="center")
		self.load_assests(32)  # hard coded for now, should relative to 32 pixels of 1080 pixel height screen

		# draw first img, then get all paths in dir
		current_image = self.ImagePath(image_path_raw[image_path_raw.rfind('/')+1:])
		self.files = [current_image]
		self.image_loader()
		self.app.update()
		self.files: list[self.ImagePath] = []
		for p in next(os.walk(self.image_directory), (None, None, []))[2]:
			fp = self.ImagePath(p)
			if fp.suffix in self.VALID_FILE_TYPES:
				self.files.append(fp)
		self.files.sort(key=self.IKey)
		self.cur_index = self.binary_search(current_image.name)
		self.full_path = f'{self.image_directory}{self.files[self.cur_index].name}'
		ImageDraw.ImageDraw.font = ImageFont.truetype("arial.ttf", self.scale_pixels_to_screen(22))  # font for drawing on images
		ImageDraw.ImageDraw.fontmode = 'L'  # antialiasing

		# events based on input
		self.KEY_MAPPING = {'r': self.toggle_show_rename_window, "Left": self.arrow, "Right": self.arrow}  # allowed only in main app
		self.KEY_MAPPING_LIMITED = {"F2": self.toggle_show_rename_window, "Up": self.hide_topbar, "Down": self.show_topbar}  # allowed in entry or main app
		self.canvas.tag_bind(background, "<Button-1>", self.handle_click)
		self.canvas.tag_bind(self.image_display, "<Button-1>", self.handle_click)
		self.app.bind('<FocusIn>', self.redraw)
		self.app.bind('<MouseWheel>', self.scroll)
		self.app.bind('<Escape>', self.escape_button)
		self.app.bind('<KeyRelease>', self.handle_all_keybinds)

		self.app.mainloop()

	# Normalize all pixels relative to a 1080 pixel tall screen
	def scale_pixels_to_screen(self, original_pixels: int) -> int:
		return original_pixels*self.screen_h//1080

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
		self.canvas.itemconfig(self.inp, state="hidden")
		self.app.focus()

	# move to next image, dir shoud be either -1 or 1 to move left or right
	def move(self, dir: int) -> None:
		self.hide_rename_window()
		self.cur_index += dir
		if self.cur_index < 0:
			self.cur_index = len(self.files)-1
		elif self.cur_index >= len(self.files):
			self.cur_index = 0
		self.image_loader_safe()
		if self.topbar_shown:
			self.refresh_topbar()

	# redraws image if bit size of cached image is different than file that currently has that name
	# This happens if user perhaps deleted image and named a new file with the same name
	def redraw(self, event: Event) -> None:
		if event.widget is not self.app or not self.redraw_screen:
			return
		self.redraw_screen = False
		if os.path.isfile(self.full_path) and os.path.getsize(self.full_path) == self.bit_size:
			return
		self.image_loader_safe()

	# The only massive function, draws all icons on header
	def load_assests(self, topbar_height) -> None:
		# color constants
		LINE_RGB: tuple = (170, 170, 170)
		ICON_RGB: tuple = (100, 104, 102)
		ICON_HOVERED_RGB: tuple = (95, 92, 88)
		TOPBAR_RGBA: tuple = (60, 60, 60, 170)
		FONT: str = 'arial 11'

		# create stuff on topbar
		self.topbar = ImageTk.PhotoImage(Image.new("RGBA", (self.screen_w, topbar_height), TOPBAR_RGBA))
		exitb = ImageTk.PhotoImage(Image.new("RGB", (topbar_height, topbar_height), (190, 40, 40)))
		draw = ImageDraw.Draw(Image.new("RGB", (topbar_height, topbar_height), (180, 25, 20)))
		draw.line((6, 6, 26, 26), width=2, fill=LINE_RGB)
		draw.line((6, 26, 26, 6), width=2, fill=LINE_RGB)
		hoveredExit = ImageTk.PhotoImage(draw._image)
		loadedImgDef = Image.new("RGB", (topbar_height, topbar_height), ICON_RGB)  # default icon background
		loadedImgHov = Image.new("RGB", (topbar_height, topbar_height), ICON_HOVERED_RGB)  # hovered icon background
		draw = ImageDraw.Draw(loadedImgDef.copy())
		draw.line((6, 24, 24, 24), width=2, fill=LINE_RGB)
		minib = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov.copy())
		draw.line((6, 24, 24, 24), width=2, fill=LINE_RGB)
		hoveredMini = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgDef.copy())
		draw.line((9, 9, 9, 22), width=2, fill=LINE_RGB)
		draw.line((21, 9, 21, 22), width=2, fill=LINE_RGB)
		draw.line((9, 22, 21, 22), width=2, fill=LINE_RGB)
		draw.line((7, 9, 24, 9), width=2, fill=LINE_RGB)
		draw.line((12, 8, 19, 8), width=3, fill=LINE_RGB)
		trashb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov.copy())
		draw.line((9, 9, 9, 22), width=2, fill=LINE_RGB)
		draw.line((21, 9, 21, 22), width=2, fill=LINE_RGB)
		draw.line((9, 22, 21, 22), width=2, fill=LINE_RGB)
		draw.line((7, 9, 24, 9), width=2, fill=LINE_RGB)
		draw.line((12, 8, 19, 8), width=3, fill=LINE_RGB)
		hoverTrash = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgDef.copy())
		draw.line((6, 11, 16, 21), width=2, fill=LINE_RGB)
		draw.line((16, 21, 26, 11), width=2, fill=LINE_RGB)
		self.dropb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov.copy())
		draw.line((6, 11, 16, 21), width=2, fill=LINE_RGB)
		draw.line((16, 21, 26, 11), width=2, fill=LINE_RGB)
		self.hoverDrop = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgDef)
		draw.line((6, 21, 16, 11), width=2, fill=LINE_RGB)
		draw.line((16, 11, 26, 21), width=2, fill=LINE_RGB)
		draw.line((16, 11, 16, 11), width=1, fill=LINE_RGB)
		self.upb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov)
		draw.line((6, 21, 16, 11), width=2, fill=LINE_RGB)
		draw.line((16, 11, 26, 21), width=2, fill=LINE_RGB)
		draw.line((16, 11, 16, 11), width=1, fill=LINE_RGB)
		self.hoverUp = ImageTk.PhotoImage(draw._image)
		base_RGBA_image: Image = Image.new("RGBA", (topbar_height, topbar_height), (0, 0, 0, 0))  # rename button background
		draw = ImageDraw.Draw(base_RGBA_image.copy())
		draw.rectangle((7, 10, 25, 22), width=1, outline=LINE_RGB)
		draw.line((7, 16, 16, 16), width=3, fill=LINE_RGB)
		draw.line((16, 8, 16, 24), width=2, fill=LINE_RGB)
		rename_button_image: ImageTk.PhotoImage = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(base_RGBA_image)
		draw.rectangle((4, 5, 28, 27), width=1, fill=ICON_HOVERED_RGB)
		draw.rectangle((7, 10, 25, 22), width=1, outline=LINE_RGB)
		draw.line((7, 16, 16, 16), width=3, fill=LINE_RGB)
		draw.line((16, 8, 16, 24), width=2, fill=LINE_RGB)
		hoverRename = ImageTk.PhotoImage(draw._image)

		# create the topbar
		self.canvas.create_image(0, 0, image=self.topbar, anchor="nw", tag="topbar", state="hidden")
		self.file_name_display_text: int = self.canvas.create_text(36, 5, text='', fill="white", anchor="nw", font=FONT, tag="topbar", state="hidden")
		self.rename_button: int = self.canvas.create_image(0, 0, image=rename_button_image, anchor="nw", tag="topbar", state="hidden")
		exit_button_id: int = self.canvas.create_image(self.screen_w, 0, image=exitb, anchor="ne", tag="topbar", state="hidden")
		minimize_button_id: int = self.canvas.create_image(self.screen_w-topbar_height, 0, image=minib, anchor="ne", tag="topbar", state="hidden")
		trash_button_id: int = self.canvas.create_image(0, 0, image=trashb, anchor="nw", tag="topbar", state="hidden")

		self.canvas.tag_bind(exit_button_id, "<Button-1>", self.exit)
		self.canvas.tag_bind(minimize_button_id, "<Button-1>", self.minimize)
		self.canvas.tag_bind(trash_button_id, "<Button-1>", self.trash_image)
		self.canvas.tag_bind(self.rename_button, "<Button-1>", self.toggle_show_rename_window)
		self.canvas.tag_bind(exit_button_id, "<Enter>", lambda e: self.hover(exit_button_id, hoveredExit))
		self.canvas.tag_bind(exit_button_id, "<Leave>", lambda e: self.hover(exit_button_id, exitb))
		self.canvas.tag_bind(minimize_button_id, "<Enter>", lambda e: self.hover(minimize_button_id, hoveredMini))
		self.canvas.tag_bind(minimize_button_id, "<Leave>", lambda e: self.hover(minimize_button_id, minib))
		self.canvas.tag_bind(trash_button_id, "<Enter>", lambda e: self.hover(trash_button_id, hoverTrash))
		self.canvas.tag_bind(trash_button_id, "<Leave>", lambda e: self.hover(trash_button_id, trashb))
		self.canvas.tag_bind(self.rename_button, "<Enter>", lambda e: self.hover(self.rename_button, hoverRename))
		self.canvas.tag_bind(self.rename_button, "<Leave>", lambda e: self.hover(self.rename_button, rename_button_image))

		# details dropdown
		self.dbox: int = self.canvas.create_image(self.screen_w-topbar_height-topbar_height, 0, image=self.dropb, anchor="ne", tag="topbar", state="hidden")
		self.canvas.tag_bind(self.dbox, "<Button-1>", self.toggle_details_dropdown)
		self.canvas.tag_bind(self.dbox, "<Enter>", self.hover_dropdown_toggle)
		self.canvas.tag_bind(self.dbox, "<Leave>", self.leave_hover_dropdown_toggle)
		self.infod: int = self.canvas.create_image(self.screen_w, topbar_height, anchor="ne", tag="topbar", state="hidden")

		# rename window
		self.inp: int = self.canvas.create_window(0, 0, width=200, height=24, anchor="nw")
		self.rename_entry: Entry = Entry(self.app, font=FONT)
		self.rename_entry.bind("<Return>", self.try_rename_or_convert)
		self.rename_entry.bind("<KeyRelease>", self.handle_limited_keybinds)
		self.rename_entry.bind("<Control-c>", self.copy_to_clipboard)
		self.canvas.itemconfig(self.inp, state="hidden", window=self.rename_entry)

	# tkinter's entry seems broken and ctrl+c doesn't work so I have to implement it myself
	def copy_to_clipboard(self, event: Event = None) -> None:
		if self.canvas.itemcget(self.inp, "state") == "hidden" or not self.rename_entry.select_present():
			return
		pyperclip.copy(self.rename_entry.selection_get())

	# wrapper for exit function to close rename window first if its open
	def escape_button(self, event: Event = None) -> None:
		if self.canvas.itemcget(self.inp, "state") == "normal":
			self.hide_rename_window()
			return
		self.exit()

	# properly exit program
	def exit(self, event: Event = None) -> None:
		self.canvas.delete(self.file_name_display_text)
		self.app.quit()
		self.app.destroy()
		exit(0)

	def hover(self, id: str, img: ImageTk.PhotoImage) -> None:
		self.canvas.itemconfig(id, image=img)

	def leave_hover_dropdown_toggle(self, event: Event = None) -> None:
		self.canvas.itemconfig(self.dbox, image=self.upb if self.dropdown_shown else self.dropb)

	def hover_dropdown_toggle(self, event: Event = None) -> None:
		self.canvas.itemconfig(self.dbox, image=self.hoverUp if self.dropdown_shown else self.hoverDrop)

	def trash_image(self, event: Event = None) -> None:
		self.clear_animation_variables()
		send2trash(os.path.abspath(self.full_path))  # had errors in windows without abspath
		self.hide_rename_window()
		self.remove_image_and_move_to_next()

	def toggle_show_rename_window(self, event: Event = None) -> None:
		if self.canvas.itemcget(self.inp, "state") == "normal":
			self.hide_rename_window()
			return

		if self.canvas.itemcget("topbar", "state") == "hidden":
			self.show_topbar()
		self.canvas.itemconfig(self.inp, state="normal")
		self.canvas.coords(self.inp, self.rename_window_x_offset+40, 4)
		self.rename_entry.focus()

	def cleanup_after_rename(self, newname: str) -> None:
		newnameObj = self.ImagePath(newname)
		self.files.insert(self.binary_search(newnameObj.name), newnameObj)
		self.hide_rename_window()
		self.image_loader_safe()
		self.refresh_topbar()

	# asks os to rename file and changes position in list to new location
	def rename_image(self, newname: str, newPath: str) -> None:
		if os.path.isfile(newPath) or os.path.isdir(newPath):
			raise FileExistsError()

		# need to close: would be open if currently loading GIF frames
		self.temp.close()
		os.rename(self.full_path, newPath)
		self.remove_image()
		self.cleanup_after_rename(newname)

	# returns bool of successful conversion
	def convert_file_and_save_new(self, newname: str, newPath: str, imageExtension: str) -> bool:
		if os.path.isfile(newPath) or os.path.isdir(newPath):
			raise FileExistsError()

		with open(self.full_path, mode="rb") as fp:
			with Image.open(fp) as temp_img:
				# refuse to convert animations for now
				if (getattr(temp_img, "n_frames", 1) > 1):
					return False

				match imageExtension:
					case ".webp":
						temp_img.save(newPath, "WebP", quality=100, method=6)
					case ".png":
						temp_img.save(newPath, "PNG", optimize=True)
					case ".bmp":
						temp_img.save(newPath, "BMP")
					case ".jpg" | ".jpeg" | ".jif" | ".jfif" | ".jpe":  # any JPEG variation
						if self.files[self.cur_index].name[0] == 'j':
							return False
						temp_img.save(newPath, "JPEG", optimize=True, quality=100)
					case _:
						return False

				fp.flush()

		if askyesno("Confirm deletion", f"Converted file to {imageExtension}, delete old file?"):
			self.trash_image()
		self.cleanup_after_rename(newname)
		return True

	def try_rename_or_convert(self, event: Event = None) -> None:
		if self.canvas.itemcget(self.inp, "state") == "hidden":
			return

		# make a new name removing illegal char for current OS
		# technically windows allows spaces at end of name but thats a bit silly so strip anyway
		new_name: str = sub(self.OS_illegal_chars, "", self.rename_entry.get().strip())

		new_image_extension: str = new_name[new_name.rfind('.', -5):]

		# if the extension is valid, try to convert
		# otherwise use old extension and rename the file
		try:
			if new_image_extension != self.files[self.cur_index].suffix:
				if new_image_extension in self.VALID_FILE_TYPES and self.convert_file_and_save_new(new_name, f'{self.image_directory}{new_name}', new_image_extension):
					return
				new_name += self.files[self.cur_index].suffix
			self.rename_image(new_name, f'{self.image_directory}{new_name}')
		except Exception:
			self.rename_entry.config(bg="#e6505f")  # flash red to tell user program couldn't rename
			self.app.after(400, lambda: self.rename_entry.config(bg="white"))

	def minimize(self, event: Event) -> None:
		self.redraw_screen = True
		self.app.iconify()

	def get_image_fit_to_screen(self, interpolation: int, dimensions: tuple[int, int]) -> ImageTk.PhotoImage:
		# simplejpeg is faster way of decoding to numpy array
		if self.temp.format == "JPEG":
			with open(self.full_path, "rb") as im:
				return ImageTk.PhotoImage(Image.fromarray(cv2.resize(simplejpeg.decode_jpeg(im.read()), dimensions, interpolation=interpolation)))
		# This cv2 resize is faster than PIL, but convert from mode P to RGB then resize is slower. Yet, PIL resize for P mode images looks very bad so still use cv2
		return ImageTk.PhotoImage(Image.fromarray(cv2.resize(asarray(self.temp if self.temp.mode != 'P' else self.temp.convert("RGB"), order='C'), dimensions, interpolation=interpolation)))

	def dimension_finder(self) -> tuple[int, int]:
		width: int = round(self.trueWidth * (self.screen_h/self.trueHeight))

		# fit to height if width in screen, else fit to width and let height go off screen
		return (width, self.screen_h) if width <= self.screen_w else (self.screen_w, round(self.trueHeight * (self.screen_w/self.trueWidth)))

	# loads and displays an image
	def image_loader(self) -> None:
		current_img = self.files[self.cur_index]
		self.full_path = f"{self.image_directory}{self.files[self.cur_index].name}"

		try:
			# open even if in cache to throw error if user deleted it outside of program
			self.temp = Image.open(self.full_path)
		except (FileNotFoundError, UnidentifiedImageError):
			self.remove_image_and_move_to_next()
			return

		self.bit_size: int = os.path.getsize(self.full_path)

		# check if was cached and not changed outside of program
		cached_img_data = self.cache.get(current_img.name, None)
		if cached_img_data is not None and self.bit_size == cached_img_data.bit_size:
			self.trueWidth, self.trueHeight, self.trueSize, self.conImg = cached_img_data.width, cached_img_data.height, cached_img_data.size_as_text, cached_img_data.image
			self.temp.close()
		else:
			self.trueWidth, self.trueHeight = self.temp.size
			size_kb: int = self.bit_size >> 10
			self.trueSize = f"{round(size_kb/10.24)/100}mb" if size_kb > 999 else f"{size_kb}kb"
			dimensions = self.dimension_finder()
			frame_count: int = getattr(self.temp, "n_frames", 1)
			interpolation: int = cv2.INTER_AREA if self.trueHeight > self.screen_h else cv2.INTER_CUBIC
			self.conImg = self.get_image_fit_to_screen(interpolation, dimensions)

			# special case, file is animated
			if frame_count > 1:
				self.aniamtion_frames = [None] * frame_count
				self.aniamtion_frames[0] = self.conImg
				Thread(target=self.load_frame, args=(1, dimensions, current_img.name, interpolation), daemon=True).start()
				# find animation frame speed
				try:
					speed = int(self.temp.info["duration"] * self.ANIMATION_SPEED_FACTOR)
					if speed < 2:
						speed = self.DEFAULT_SPEED
				except (KeyError, AttributeError):
					speed = self.DEFAULT_SPEED

				self.animation_id = self.app.after(speed+20, self.animate, 1, speed)
			else:
				# cache non-animated images
				self.cache[current_img.name] = self.CachedImage(self.trueWidth, self.trueHeight, self.trueSize, self.conImg, self.bit_size)
				self.temp.close()
		self.canvas.itemconfig(self.image_display, image=self.conImg)
		self.app.title(current_img.name)

	# call this when an animation might have been playing before you need to load a new image
	def image_loader_safe(self) -> None:
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
		if self.topbar_shown:
			self.hide_topbar()
		else:
			self.show_topbar()

	def remove_image(self) -> None:
		# delete image from files array and from cache if present
		self.cache.pop(self.files.pop(self.cur_index).name, None)

	def remove_image_and_move_to_next(self) -> None:
		self.remove_image()

		number_of_images: int = len(self.files)
		if number_of_images == 0:
			self.exit()
		if self.cur_index >= number_of_images:
			self.cur_index = number_of_images - 1

		self.image_loader()
		if self.topbar_shown:
			self.refresh_topbar()

	def refresh_topbar(self) -> None:
		self.canvas.itemconfig(self.file_name_display_text, text=self.files[self.cur_index].name)
		self.rename_window_x_offset = self.canvas.bbox(self.file_name_display_text)[2]
		self.canvas.coords(self.rename_button, self.rename_window_x_offset, 0)
		self.create_details_dropdown() if self.dropdown_shown else self.canvas.itemconfig(self.infod, state="hidden")

	''' displays a frame on screen and recursively calls itself on next frame
		frame_index: index of current frame to be displayed
		speed: speed in ms until next frame
	'''
	def animate(self, frame_index: int, speed: int) -> None:
		frame_index += 1
		if frame_index >= len(self.aniamtion_frames):
			frame_index = 0

		ms_until_next_frame: int = speed
		current_frame: ImageTk.PhotoImage = self.aniamtion_frames[frame_index]
		# if tried to show next frame before it is loaded, reset to current frame and try again after delay
		if current_frame is None:
			frame_index -= 1
			ms_until_next_frame += 10
		else:
			self.canvas.itemconfig(self.image_display, image=current_frame)

		self.animation_id = self.app.after(ms_until_next_frame, self.animate, frame_index, speed)

	def load_frame(self, frame_index: int, dimensions: tuple[int, int], file_name: str, interpolation: int) -> None:
		# if moved to new image, don't keep loading previous animated image
		if file_name != self.files[self.cur_index].name:
			return
		try:
			self.temp.seek(frame_index)
			self.aniamtion_frames[frame_index] = self.get_image_fit_to_screen(interpolation, dimensions)
			self.load_frame(frame_index+1, dimensions, file_name, interpolation)
		except Exception:
			# scrolling, recursion ending, etc cause variety of errors. Catch and close if thread was for current animation
			if file_name == self.files[self.cur_index].name:
				self.temp.close()

	# cleans up after an animated file was opened
	def clear_animation_variables(self) -> None:
		if self.animation_id == "":
			return

		self.app.after_cancel(self.animation_id)
		self.animation_id = ""
		self.aniamtion_frames.clear()
		self.temp.close()

	def toggle_details_dropdown(self, event: Event) -> None:
		self.dropdown_shown = not self.dropdown_shown
		self.hover_dropdown_toggle()  # fake mouse hover
		self.create_details_dropdown() if self.dropdown_shown else self.canvas.itemconfig(self.infod, state="hidden")

	def create_details_dropdown(self) -> None:
		image_dimension_text: str = f"Pixels: {self.trueWidth}x{self.trueHeight}"

		text_bbox: tuple = ImageDraw.ImageDraw.font.getbbox(image_dimension_text)

		box_to_draw_on: ImageDraw = ImageDraw.Draw(Image.new("RGBA", (text_bbox[2]+20, text_bbox[3] * 5 + 10), (40, 40, 40, 170)))
		box_to_draw_on.text((10, text_bbox[3] + 5), image_dimension_text, fill="white")
		box_to_draw_on.text((10, int(text_bbox[3]*3)), f"Size: {self.trueSize}", fill="white")

		self.dropdown_image = ImageTk.PhotoImage(box_to_draw_on._image)
		self.canvas.itemconfig(self.infod, image=self.dropdown_image, state="normal")

	''' find index of image in the sorted list of all images in the directory
	target_image: name of image file to find
	'''
	def binary_search(self, target_image: str) -> int:
		low, high = 0, len(self.files)-1
		while low <= high:
			mid = (low+high) >> 1
			current_image = self.files[mid].name
			if target_image == current_image:
				return mid
			if utilHelper.my_cmp_w(target_image, current_image):
				high = mid-1
			else:
				low = mid+1
		return low


if __name__ == "__main__":
	DEBUG: bool = True
	if len(argv) > 1:
		Viewer(argv[1])
	elif DEBUG:
		from time import perf_counter_ns, sleep  # noqa: F401 DEBUG
		Viewer(r"C:\Users\jimde\OneDrive\Pictures\myself.jpg")  # DEBUG
	else:
		print("An Image Viewer written in Python\nRun with 'python -m viewer \"C:/path/to/an/image\"' or convert to an exe and select \"open with\" on your image")
