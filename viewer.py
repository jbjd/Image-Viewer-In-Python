# python -m nuitka --windows-disable-console --windows-icon-from-ico="C:\PythonCode\Viewer\icon\icon.ico" --mingw64 viewer.py
from sys import argv  # std
from tkinter import Tk, Canvas, Entry  # std
from threading import Thread  # std
from pathlib import Path  # std
from os import rename, name  # std
comparer = lambda a, b: a<b
if name == 'nt':
	from ctypes import windll  # std
	comparer = lambda a, b: windll.shlwapi.StrCmpLogicalW(a, b) < 0	
from PIL import Image, ImageTk, ImageDraw, ImageFont, UnidentifiedImageError  # 9.3.0
from send2trash import send2trash  # 1.8.0
#from time import perf_counter_ns

# constants
SPACE: int = 32
FILETYPE: set = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".jfif"}
FONT: str = 'arial 11'
DEFAULTSPEED: int = 90
GIFSPEED: float = .88

nearest, converts = {"1", "P"}, {"LA": "La", "RGBA": "RGBa"}
# resize PIL image object, modified version of PIL source
def resize(img: Image, size: tuple[int, int], resample: int):
	box = (0, 0)+img.size
	if img.mode in nearest:
		resample = 0

	img.load()
	if img.mode in converts and resample != 0:
		return img.convert(converts[img.mode])._new(img.im.resize(size, resample, box)).convert(img.mode)

	return img._new(img.im.resize(size, resample, box))

# struct for holding cached images
class cached:
	# width, height, bit size string, PhotoImage, bits size int
	__slots__ = ('tw', 'th', 'ts', 'im', 'bits')
	def __init__(self, tw, th, ts, im, bits):
		self.tw: int = tw
		self.th: int = th
		self.ts: str = ts
		self.im: ImageTk.PhotoImage = im
		self.bits: int = bits

# key for sorting on windows
class WKey:
	__slots__ = ['pth']
	def __init__(self, pth):
		self.pth = pth.name
	def __lt__(self, b):
		return comparer(self.pth, b.pth)

class viewer:
	__slots__ = ('drawtop', 'dropDown', 'needRedraw', 'dropImage', 'trueWidth', 'trueHeigh', 'loc', 'bitSize', 'trueSize', 'gifFrames', 'gifId', 'buffer', 'app', 'cache', 'canvas', 'appw', 'apph', 'drawnImage', 'files', 'curInd', 'topbar', 'dropbar', 'text', 'dropb', 'hoverDrop', 'upb', 'hoverUp', 'inp', 'infod', 'entryText', 'temp', 'trueHeight', 'trueWidth', 'conImg', 'dbox', 'renameButton', 'DROPDOWNWIDTH', 'DROPDOWNHEIGHT')
	def __init__(self, pth):
		# UI varaibles
		self.drawtop = self.dropDown = self.needRedraw = False  # if topbar/dropdown drawn
		self.dropImage = None  # acts as refrences to items on screen
		# data on current image
		self.trueWidth = self.trueHeigh = self.loc = self.bitSize = self.curInd = 0  # loc is x location of rename window, found dynamically
		self.trueSize: str = ''
		# gif support
		self.gifFrames: list = []
		self.gifId: str = ''  # id for gif animiation
		self.buffer: int = 100
		# main stuff
		self.app: Tk = Tk()
		self.cache: dict[cached] = {}  # cache for already rendered images
		self.canvas: Canvas = Canvas(self.app, bg='black', highlightthickness=0)
		self.canvas.pack(anchor='nw', fill='both', expand=1)
		self.app.attributes('-fullscreen', True)
		self.app.state('zoomed')
		self.app.update()  # updates winfo width and height to the current size, this is necessary
		self.appw: int = self.app.winfo_width()
		self.apph: int = self.app.winfo_height()
		self.drawnImage = self.canvas.create_image(self.appw>>1, self.apph>>1, anchor='center')  # main image, replaced as necessary
		self.DROPDOWNWIDTH: int = 195
		self.DROPDOWNHEIGHT: int = 110
		self.loadAssests()
		# draw first img, then get all paths in dir
		dir = Path(pth.parent)
		self.files = [pth]
		self.imageLoader()
		self.files: list[Path] = sorted([p for p in dir.glob("*") if p.suffix in FILETYPE], key=WKey)
		self.curInd = self.binarySearch(pth.name)
		ImageDraw.ImageDraw.font = ImageFont.truetype("arial.ttf", 22)  # font for drawing on images
		ImageDraw.ImageDraw.fontmode = "L"  # antialiasing
		# events based on input
		
		self.canvas.bind("<Button-1>", self.clickHandler)
		self.app.bind("<FocusIn>", self.redraw)
		self.app.bind("<Left>", self.arrow)
		self.app.bind("<Right>", self.arrow)
		self.app.bind("<MouseWheel>", self.scroll)
		self.app.bind("<KeyRelease>", self.keyBinds)
		self.app.mainloop()

	def keyBinds(self, e):
		if e.keycode == 27:  # Esc
			self.exit()
		if e.widget is not self.app:
			return

	def arrow(self, e):
		# only move images if user not in entry
		if e.widget is self.app:
			self.move(e, 1 if e.keysym == 'Right' else -1)

	def scroll(self, e):
		self.move(e, -1 if e.delta > 0 else 1)
		self.app.focus()

	# move to next image, dir shoud be either -1 or 1 to move left or right
	def move(self, e, dir):
		self.canvas.itemconfig(self.inp, state='hidden')
		self.curInd += dir
		if self.curInd < 0:
			self.curInd = len(self.files)-1
		elif self.curInd >= len(self.files):
			self.curInd = 0 
		self.imageLoaderSafe()
		if self.drawtop: self.updateTop()

	def redraw(self, event):
		if event.widget is not self.app or not self.needRedraw:
			return
		self.needRedraw = False
		# if size of image is differnt, new image must have replace old one outside of program, so redraw screen
		if(self.files[self.curInd].stat().st_size == self.bitSize):
			return
		self.imageLoaderSafe()

	def loadAssests(self):
		# consts
		LINECOL: tuple = (170, 170, 170)
		ICONCOL: tuple = (100, 104, 102)
		ICONHOV: tuple = (95, 92, 88)
		TOPCOL: tuple = (60, 60, 60, 170)
		# stuff on topbar
		self.topbar  = ImageTk.PhotoImage(Image.new('RGBA', (self.appw, SPACE), TOPCOL))
		self.dropbar = Image.new('RGBA', (self.DROPDOWNWIDTH, self.DROPDOWNHEIGHT), (40, 40, 40, 170))
		exitb = ImageTk.PhotoImage(Image.new('RGB', (SPACE, SPACE), (190, 40, 40)))
		draw = ImageDraw.Draw(Image.new('RGB', (SPACE, SPACE), (180, 25, 20))) 
		draw.line((6, 6, 26, 26), width=2, fill=LINECOL)
		draw.line((6, 26, 26, 6), width=2, fill=LINECOL)
		hoveredExit = ImageTk.PhotoImage(draw._image)
		loadedImgDef = Image.new('RGB', (SPACE, SPACE), ICONCOL)  # default icon background
		loadedImgHov = Image.new('RGB', (SPACE, SPACE), ICONHOV)  # hovered icon background
		draw = ImageDraw.Draw(loadedImgDef.copy()) 
		draw.line((6, 24, 24, 24), width=2, fill=LINECOL)
		minib = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov.copy()) 
		draw.line((6, 24, 24, 24), width=2, fill=LINECOL)
		hoveredMini = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgDef.copy()) 
		draw.line((9, 9, 9, 22), width=2, fill=LINECOL)
		draw.line((21, 9, 21, 22), width=2, fill=LINECOL)
		draw.line((9, 22, 21, 22), width=2, fill=LINECOL)
		draw.line((7, 9, 24, 9), width=2, fill=LINECOL)
		draw.line((12, 8, 19, 8), width=3, fill=LINECOL)
		trashb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov.copy()) 
		draw.line((9, 9, 9, 22), width=2, fill=LINECOL)
		draw.line((21, 9, 21, 22), width=2, fill=LINECOL)
		draw.line((9, 22, 21, 22), width=2, fill=LINECOL)
		draw.line((7, 9, 24, 9), width=2, fill=LINECOL)
		draw.line((12, 8, 19, 8), width=3, fill=LINECOL)
		hoverTrash = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgDef.copy()) 
		draw.line((6, 11, 16, 21), width=2, fill=LINECOL)
		draw.line((16, 21, 26, 11), width=2, fill=LINECOL)
		self.dropb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov.copy()) 
		draw.line((6, 11, 16, 21), width=2, fill=LINECOL)
		draw.line((16, 21, 26, 11), width=2, fill=LINECOL)
		self.hoverDrop = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgDef) 
		draw.line((6, 21, 16, 11), width=2, fill=LINECOL)
		draw.line((16, 11, 26, 21), width=2, fill=LINECOL)
		draw.line((16, 11, 16, 11), width=1, fill=LINECOL)
		self.upb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImgHov) 
		draw.line((6, 21, 16, 11), width=2, fill=LINECOL)
		draw.line((16, 11, 26, 21), width=2, fill=LINECOL)
		draw.line((16, 11, 16, 11), width=1, fill=LINECOL)
		self.hoverUp = ImageTk.PhotoImage(draw._image)
		loadedImg = Image.new('RGBA', (SPACE, SPACE), (0,0,0,0))  # rename button background
		draw = ImageDraw.Draw(loadedImg.copy()) 
		draw.rectangle((7, 10, 25, 22), width=1, outline=LINECOL)
		draw.line((7, 16, 16, 16), width=3, fill=LINECOL)
		draw.line((16, 8, 16, 24), width=2, fill=LINECOL)
		renameb = ImageTk.PhotoImage(draw._image)
		draw = ImageDraw.Draw(loadedImg) 
		draw.rectangle((4, 5, 28, 27), width=1, fill=ICONHOV)
		draw.rectangle((7, 10, 25, 22), width=1, outline=LINECOL)
		draw.line((7, 16, 16, 16), width=3, fill=LINECOL)
		draw.line((16, 8, 16, 24), width=2, fill=LINECOL)
		hoverRename = ImageTk.PhotoImage(draw._image)
		# topbar assests
		self.canvas.create_image(0, 0, image=self.topbar, anchor='nw', tag="topb", state='hidden')
		self.text: int = self.canvas.create_text(36, 5, text='', fill="white", anchor='nw', font=FONT, tag="topb", state='hidden')
		self.renameButton: int = self.canvas.create_image(0, 0, image=renameb, anchor='nw', tag='topb', state='hidden')
		b: int = self.canvas.create_image(self.appw, 0, image=exitb, anchor='ne', tag='topb', state='hidden')
		b2: int = self.canvas.create_image(self.appw-SPACE, 0, image=minib, anchor='ne', tag='topb', state='hidden')
		t: int = self.canvas.create_image(0, 0, image=trashb, anchor='nw', tag='topb', state='hidden')
		self.canvas.tag_bind(b, '<Button-1>', self.exit)
		self.canvas.tag_bind(b2,'<Button-1>', self.minimize)
		self.canvas.tag_bind(t, '<Button-1>', self.trashFile)
		self.canvas.tag_bind(self.renameButton, '<Button-1>', self.renameWindow)
		self.canvas.tag_bind(b, '<Enter>', lambda e: self.hover(b, hoveredExit))
		self.canvas.tag_bind(b, '<Leave>', lambda e: self.hover(b, exitb))
		self.canvas.tag_bind(b2,'<Enter>', lambda e: self.hover(b2, hoveredMini))
		self.canvas.tag_bind(b2,'<Leave>', lambda e: self.hover(b2, minib))
		self.canvas.tag_bind(t, '<Enter>', lambda e: self.hover(t, hoverTrash))
		self.canvas.tag_bind(t, '<Leave>', lambda e: self.hover(t, trashb))
		self.canvas.tag_bind(self.renameButton, '<Enter>', lambda e: self.hover(self.renameButton, hoverRename))
		self.canvas.tag_bind(self.renameButton, '<Leave>', lambda e: self.hover(self.renameButton, renameb))
		self.dbox: int = self.canvas.create_image(self.appw-SPACE-SPACE, 0, image=self.dropb, anchor='ne', tag='topb', state='hidden') 
		self.inp: int = self.canvas.create_window(0, 0, width=200, height=24, anchor='nw')  # rename window
		self.canvas.tag_bind(self.dbox, '<Button-1>', self.toggleDrop)
		self.canvas.tag_bind(self.dbox, '<Enter>', self.hoverOnDrop)
		self.canvas.tag_bind(self.dbox, '<Leave>', self.removeHoverDrop)
		# dropbox
		self.infod: int = self.canvas.create_image(self.appw, SPACE, anchor='ne', tag="topb", state='hidden')
		# rename window
		self.entryText: Entry = Entry(self.app, font=FONT)
		self.entryText.bind('<Return>', self.renameFile)
		self.canvas.itemconfig(self.inp, state='hidden', window=self.entryText)

	def exit(self, e=None):
		self.canvas.delete(self.text)
		self.app.quit()
		self.app.destroy()
		exit(0)

	# START BUTTON FUNCTIONS
	def hover(self, id, img) -> None:
		self.canvas.itemconfig(id, image=img)

	def removeHoverDrop(self, event=None) -> None:
		self.canvas.itemconfig(self.dbox, image=self.upb if self.dropDown else self.dropb)

	def hoverOnDrop(self, event=None) -> None:
		self.canvas.itemconfig(self.dbox, image=self.hoverUp if self.dropDown else self.hoverDrop)

	# delete image
	def trashFile(self, event=None) -> None:
		self.clearGif()
		send2trash(self.files[self.curInd])
		self.canvas.itemconfig(self.inp, state='hidden')
		self.removeAndMove()

	# opens tkinter entry to accept user input
	def renameWindow(self, event) -> None:
		if self.canvas.itemcget(self.inp,'state') == 'hidden':
			self.canvas.itemconfig(self.inp, state='normal')
			self.canvas.coords(self.inp, self.loc+40, 4)
			self.entryText.focus()
			return
		self.canvas.itemconfig(self.inp, state='hidden')
		self.app.focus()

	# asks os to rename file and changes position in list to new location
	def renameFile(self, event) -> None:
		if self.canvas.itemcget(self.inp,'state') == 'hidden': return
		newname = f'{self.files[self.curInd].parent}/{self.entryText.get().strip()}{self.files[self.curInd].suffix}'
		try:
			rename(self.files[self.curInd], newname) 
			newname = Path(newname)
			self.removeImg()
			self.files.insert(self.binarySearch(newname.name), newname)
			self.canvas.itemconfig(self.inp, state='hidden')
			self.app.focus()
			self.imageLoaderSafe()
			self.updateTop()
		except Exception:
			self.entryText.config(bg='#e6505f')  # flash red to tell user can't rename
			self.app.after(400, lambda : self.entryText.config(bg='white'))

	# minimizes app
	def minimize(self, event) -> None:
		self.needRedraw = True
		self.app.iconify()

	# START MAIN IMAGE FUNCTIONS
	''' w, h: width and height of image before resize
		returns tuple of what dimensions to resize too
	'''
	def dimensionFinder(self) -> tuple[int, int]:
		width = round(self.trueWidth * (self.apph/self.trueHeight))
		#  Size to height of window. If that makes the image too wide, size to width instead
		return (width, self.apph) if width <= self.appw else (self.appw, round(self.trueHeight * (self.appw/self.trueWidth)))

	# loads image path
	def imageLoader(self) -> None:
		curPath = self.files[self.curInd]
		try:
			self.temp = Image.open(curPath) # open even if in cache to interrupt if user deleted it outside of program
			self.bitSize: int = curPath.stat().st_size
			close: bool = True
			data: cached = self.cache.get(curPath, None)
			if data is not None and self.bitSize == data.bits: # was cached
				self.trueWidth, self.trueHeight, self.trueSize, self.conImg = data.tw, data.th, data.ts, data.im
			else:
				self.trueWidth, self.trueHeight = self.temp.size
				intSize: int = self.bitSize>>10
				self.trueSize = f"{round(intSize/10.24)/100}mb" if intSize > 1023 else f"{intSize}kb"
				w, h = self.dimensionFinder()
				frames: int = getattr(self.temp, 'n_frames', 0)
				if(frames > 1 and curPath.suffix != '.png'):  # any non-png animated file, animated png don't work in tkinter it seems
					self.gifFrames = [None] * frames
					try:
						speed = int(self.temp.info['duration'] * GIFSPEED)
						if speed < 2: speed = DEFAULTSPEED
					except(KeyError, AttributeError):
						speed = DEFAULTSPEED
					self.buffer = int(speed*1.4)
					self.conImg, speed = ImageTk.PhotoImage(resize(self.temp, (w, h), 2)), speed
					self.gifFrames[0] = (self.conImg, speed)
					Thread(target=self.loadFrame, args=(1, w, h, curPath.name), daemon=True).start()
					self.gifId = self.app.after(speed+28, self.animate, 1)
					close = False  # keep open since this is an animation and we need to wait thead to load frames
				else:  # any image thats not cached or animated
					self.conImg = ImageTk.PhotoImage(resize(self.temp, (w, h), 1) if h != self.trueHeight else self.temp)
					self.cache[curPath] = cached(self.trueWidth, self.trueHeight, self.trueSize, self.conImg, self.bitSize)
			self.canvas.itemconfig(self.drawnImage, image=self.conImg)
			self.app.title(curPath.name)
			if close: self.temp.close()  # closes in clearGIF function or at end of loading frames if animated, closes here otherwise
		except(FileNotFoundError, UnidentifiedImageError):
			self.removeAndMove()

	# wrapper for image loader that clears gifs before loading new image
	def imageLoaderSafe(self):
		self.clearGif()
		self.imageLoader()

	# skip clicks to menu, draws menu if not present
	def clickHandler(self, e) -> None:
		if self.drawtop and (e.y <= SPACE or (self.dropDown and e.x > self.appw-self.DROPDOWNWIDTH and e.y < SPACE+self.DROPDOWNHEIGHT)):
			return
		self.drawtop = not self.drawtop
		self.app.focus()
		if self.drawtop: 
			self.canvas.itemconfig("topb", state='normal')
			self.updateTop()
		else: 
			self.canvas.itemconfig("topb", state='hidden')
			self.canvas.itemconfig(self.inp, state='hidden')

	def removeImg(self) -> None:
		# delete image from files array and from cache if present
		self.cache.pop(self.files.pop(self.curInd), None)

	# remove from list and move to next image
	def removeAndMove(self) -> None:
		self.removeImg()
		size = len(self.files)
		if size == 0: self.exit()
		if self.curInd >= size: self.curInd = size-1
		self.imageLoader()
		if self.drawtop: self.updateTop()

	def updateTop(self) -> None:
		self.canvas.itemconfig(self.text, text=self.files[self.curInd].name)
		self.loc = self.canvas.bbox(self.text)[2]
		self.canvas.coords(self.renameButton, self.loc, 0)
		if self.dropDown: self.createDropbar()
	# END MAIN IMAGE FUNCTIONS

	# START GIF FUNCTIONS
	def animate(self, gifFrame: int) -> None:
		gifFrame += 1
		if gifFrame >= len(self.gifFrames): gifFrame = 0

		try:
			img, speed = self.gifFrames[gifFrame]
			self.canvas.itemconfig(self.drawnImage, image=img)
		except TypeError:
			speed = self.buffer
			gifFrame -= 1
			self.buffer += 10
		
		self.gifId = self.app.after(speed, self.animate, gifFrame)

	def loadFrame(self, gifFrame: int, w: int, h: int, name):
		# move function would have already closed old gif, so if new gif on screen, don't keep loading previous gif
		if name != self.files[self.curInd].name: return
		try:
			self.temp.seek(gifFrame)
			try:
				speed = int(self.temp.info['duration'] * GIFSPEED)
				if speed < 2: speed = DEFAULTSPEED
			except(KeyError, AttributeError):
				speed = DEFAULTSPEED
			self.buffer = int(speed*1.4)
			self.gifFrames[gifFrame] = (ImageTk.PhotoImage(resize(self.temp, (w, h), 2)), speed)
			self.loadFrame(gifFrame+1, w, h, name)
		except Exception:  
			# scroll, recursion ending, etc. get variety of errors. Catch and close if thread is for current GIF
			if name == self.files[self.curInd].name: self.temp.close()

	def clearGif(self) -> None:
		if self.gifId == '': return
		self.app.after_cancel(self.gifId)
		self.gifId = ''
		self.gifFrames.clear()
		self.temp.close()
	# END GIF FUNCTIONS  

	# START DROPDOWN FUNCTIONS
	def toggleDrop(self, event=None) -> None:
		self.dropDown = not self.dropDown
		self.hoverOnDrop()
		self.createDropbar() if self.dropDown else self.canvas.itemconfig(self.infod, state='hidden')
		
	def createDropbar(self) -> None:
		draw = ImageDraw.Draw(self.dropbar.copy())  # copy plain window and draw on it
		draw.text((10, 25), f"Pixels: {self.trueWidth}x{self.trueHeight}", fill="white")
		draw.text((10, 60), f"Size: {self.trueSize}", fill="white")
		self.dropImage = ImageTk.PhotoImage(draw._image)
		self.canvas.itemconfig(self.infod, image=self.dropImage, state='normal')
	# END DROPDOWN FUNCTIONS

	# pth: Path object of path to current image 
	def binarySearch(self, pth):
		low, high = 0, len(self.files)-1
		while low <= high:
			mid = (low+high)>>1
			cur = self.files[mid].name
			if pth == cur: return mid
			if comparer(pth, cur): high = mid-1
			else: low = mid+1
		return low

if __name__ == "__main__":
	DEBUG: bool = False
	if len(argv) > 1 or DEBUG:
		pathToImage = Path(r"C:\Users\jimde\OneDrive\Pictures\test.jpg" if DEBUG else argv[1])
		if pathToImage.suffix not in FILETYPE: exit(0)
		viewer(pathToImage)
