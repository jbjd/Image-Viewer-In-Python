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

exePath: str = argv[0].replace('\\', '/')
exePath = exePath[:exePath.rfind('/')+1]
if os.name == 'nt':
	from ctypes import windll
	class WinUtil():
		__slots__ = ()
		def myCmpW(self, a, b):
			return windll.shlwapi.StrCmpLogicalW(a, b) < 0
	utilHelper = WinUtil()
else:
	# default functions, currently only support windows
	class DefaultUtil():
		__slots__ = ()
		def myCmpW(self, a, b):
			if a == b: return 0
			return a < b
	utilHelper = DefaultUtil()

class viewer:
	# class vars
	DROPDOWNHEIGHT: int = 110
	DEFAULTSPEED: int = 90
	GIFSPEED: float = .75
	SPACE: int = 32
	VALID_FILE_TYPES: set[str] = {".png", ".jpg", ".jpeg", ".jfif", ".jif", ".jpe", ".webp", ".gif", ".bmp"}  # valid image types

	# struct for holding cached images, for some reason this stores less data than a regular tuple based on my tests
	class cached:
		# width, height, bit size string, PhotoImage, bits size int
		__slots__ = ('tw', 'th', 'ts', 'im', 'bits')
		def __init__(self, tw, th, ts, im, bits):
			self.tw: int = tw
			self.th: int = th
			self.ts: str = ts
			self.im: ImageTk.PhotoImage = im
			self.bits: int = bits

	class ImagePath():
		__slots__ = ('suffix', 'name')
		def __init__(self, name: str):
			self.suffix = name[name.rfind('.'):].lower()
			self.name = name

	# key for sorting
	class IKey:
		__slots__ = ('path')
		def __init__(self, path: str):
			self.path: str = path.name
		def __lt__(self, b):
			return utilHelper.myCmpW(self.path, b.path)

	__slots__ = ('illegalChar', 'fullname', 'dir', 'drawtop', 'dropDown', 'needRedraw', 'dropImage', 'trueWidth', 'trueHeigh', 'renameWindowLocation', 'bitSize', 'trueSize', 'gifFrames', 'gifId', 'app', 'cache', 'canvas', 'appw', 'apph', 'drawnImage', 'files', 'curInd', 'topbar', 'dropbar', 'text', 'dropb', 'hoverDrop', 'upb', 'hoverUp', 'inp', 'infod', 'entryText', 'temp', 'trueHeight', 'trueWidth', 'conImg', 'dbox', 'renameButton', 'KEY_MAPPING', 'KEY_MAPPING_LIMITED')
	def __init__(self, rawPath: str):
		rawPath = rawPath.replace('\\', '/')
		# Make sure user ran with a supported image
		if not os.path.isfile(rawPath) or rawPath[rawPath.rfind('.'):] not in self.VALID_FILE_TYPES: exit(0)
		self.dir: str = rawPath[:rawPath.rfind('/')+1]
		pth = self.ImagePath(rawPath[rawPath.rfind('/')+1:])
		# UI varaibles
		self.drawtop: bool
		self.dropDown: bool
		self.needRedraw: bool
		self.drawtop = self.dropDown = self.needRedraw = False  # if topbar/dropdown drawn
		self.dropImage = None  # acts as refrences to items on screen
		# data on current image
		self.trueWidth: int
		self.trueHeigh: int
		self.renameWindowLocation: int
		self.bitSize: int
		self.curInd: int
		self.trueWidth = self.trueHeigh = self.renameWindowLocation = self.bitSize = self.curInd = 0  # loc is x location of rename window, found dynamically
		self.trueSize: str = ''
		# gif support
		self.gifFrames: list = []
		self.gifId: str = ''  # id for gif animiation
		# main stuff
		self.app: Tk = Tk()
		if os.name == 'nt':
			self.app.iconbitmap(default=f'{exePath}icon/icon.ico')
			self.illegalChar: str = '[\\\\/<>:"|?*]'
		else:
			self.illegalChar: str = '[/]'
		self.cache: dict[str, self.cached] = {}  # cache for already rendered images
		self.canvas: Canvas = Canvas(self.app, bg='black', highlightthickness=0)
		self.canvas.pack(anchor='nw', fill='both', expand=1)
		self.app.attributes('-fullscreen', True)
		self.app.state('zoomed')
		self.app.update()  # updates winfo width and height to the current size, this is necessary
		self.appw: int = self.app.winfo_width()
		self.apph: int = self.app.winfo_height()
		background = self.canvas.create_rectangle(0,0,self.appw,self.apph,fill='black')
		self.drawnImage = self.canvas.create_image(self.appw>>1, self.apph>>1, anchor='center')  # main image, replaced as necessary
		
		self.loadAssests()
		# draw first img, then get all paths in dir
		self.files = [pth]
		self.imageLoader()
		self.app.update()
		self.files: list[self.ImagePath] = []
		for p in next(os.walk(self.dir), (None, None, []))[2]:
			fp = self.ImagePath(p)
			if fp.suffix in self.VALID_FILE_TYPES: self.files.append(fp)
		self.files.sort(key=self.IKey)
		self.curInd = self.binarySearch(pth.name)
		self.fullname = f'{self.dir}{self.files[self.curInd].name}'
		ImageDraw.ImageDraw.font = ImageFont.truetype('arial.ttf', 22*self.apph//1080)  # font for drawing on images
		ImageDraw.ImageDraw.fontmode = 'L'  # antialiasing
		# events based on input
		self.KEY_MAPPING = {'r': self.renameWindow, 'Left': self.arrow, 'Right': self.arrow}  # allowed only in main app
		self.KEY_MAPPING_LIMITED = {'F2': self.renameWindow, 'Up': self.hideWrapper, 'Down': self.showWrapper}  # allowed in entry or main app
		self.canvas.tag_bind(background, '<Button-1>', self.clickHandler)
		self.canvas.tag_bind(self.drawnImage, '<Button-1>', self.clickHandler)
		self.app.bind('<FocusIn>', self.redraw)
		self.app.bind('<MouseWheel>', self.scroll)
		self.app.bind('<Escape>', self.escButton)
		self.app.bind('<KeyRelease>', self.keyBinds)
		if os.path.isfile("icon/icon.ico"):
			self.app.iconbitmap("icon/icon.ico")
		self.app.mainloop()

	def keyBinds(self, e: Event) -> None:
		if e.widget is self.app:
			if e.keysym in self.KEY_MAPPING:
				self.KEY_MAPPING[e.keysym](e)
			else:
				self.keyBindsLimited(e)
		
	def keyBindsLimited(self, e: Event) -> None:
		if e.keysym in self.KEY_MAPPING_LIMITED:
			self.KEY_MAPPING_LIMITED[e.keysym](e)

	def arrow(self, e: Event) -> None:
		# only move images if user not in entry
		if e.widget is self.app:
			self.move(1 if e.keysym == 'Right' else -1)

	def scroll(self, e: Event) -> None:
		self.move(-1 if e.delta > 0 else 1)

	def hideRenameWindow(self) -> None:
		self.canvas.itemconfig(self.inp, state='hidden')
		self.app.focus()

	# move to next image, dir shoud be either -1 or 1 to move left or right
	def move(self, dir: int) -> None:
		self.hideRenameWindow()
		self.curInd += dir
		if self.curInd < 0:
			self.curInd = len(self.files)-1
		elif self.curInd >= len(self.files):
			self.curInd = 0 
		self.imageLoaderSafe()
		if self.drawtop: self.updateTop()

	# redraws image if bitsize of cached image is different than file that currently has that name
	# This happens if user perhaps deleted image and named a new file with the same name
	def redraw(self, e: Event) -> None:
		if e.widget is not self.app or not self.needRedraw:
			return
		self.needRedraw = False
		# if size of image is differnt, new image must have replace old one outside of program, so redraw screen
		if(os.path.isfile(self.fullname) and os.path.getsize(self.fullname) == self.bitSize):
			return
		self.imageLoaderSafe()

	# The only massive function, draws all icons on header
	def loadAssests(self) -> None:
		# consts
		LINECOL: tuple = (170, 170, 170)
		ICONCOL: tuple = (100, 104, 102)
		ICONHOV: tuple = (95, 92, 88)
		TOPCOL: tuple = (60, 60, 60, 170)
		FONT: str = 'arial 11'
		# stuff on topbar
		self.topbar  = ImageTk.PhotoImage(Image.new('RGBA', (self.appw, self.SPACE), TOPCOL))
		exitb = ImageTk.PhotoImage(Image.new('RGB', (self.SPACE, self.SPACE), (190, 40, 40)))
		draw = ImageDraw.Draw(Image.new('RGB', (self.SPACE, self.SPACE), (180, 25, 20))) 
		draw.line((6, 6, 26, 26), width=2, fill=LINECOL)
		draw.line((6, 26, 26, 6), width=2, fill=LINECOL)
		hoveredExit = ImageTk.PhotoImage(draw._image)
		loadedImgDef = Image.new('RGB', (self.SPACE, self.SPACE), ICONCOL)  # default icon background
		loadedImgHov = Image.new('RGB', (self.SPACE, self.SPACE), ICONHOV)  # hovered icon background
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
		loadedImg = Image.new('RGBA', (self.SPACE, self.SPACE), (0,0,0,0))  # rename button background
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
		b2: int = self.canvas.create_image(self.appw-self.SPACE, 0, image=minib, anchor='ne', tag='topb', state='hidden')
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
		self.dbox: int = self.canvas.create_image(self.appw-self.SPACE-self.SPACE, 0, image=self.dropb, anchor='ne', tag='topb', state='hidden') 
		self.inp: int = self.canvas.create_window(0, 0, width=200, height=24, anchor='nw')  # rename window
		self.canvas.tag_bind(self.dbox, '<Button-1>', self.toggleDrop)
		self.canvas.tag_bind(self.dbox, '<Enter>', self.hoverOnDrop)
		self.canvas.tag_bind(self.dbox, '<Leave>', self.removeHoverDrop)
		# dropbox
		self.infod: int = self.canvas.create_image(self.appw, self.SPACE, anchor='ne', tag="topb", state='hidden')
		# rename window
		self.entryText: Entry = Entry(self.app, font=FONT)
		self.entryText.bind('<Return>', self.tryRenameFile)
		self.entryText.bind('<KeyRelease>', self.keyBindsLimited)
		self.entryText.bind('<Control-c>', self.copyText)
		self.canvas.itemconfig(self.inp, state='hidden', window=self.entryText)

	def copyText(self, e: Event = None) -> None:
		if self.canvas.itemcget(self.inp,'state') == 'hidden' or not self.entryText.select_present():
			return
		pyperclip.copy(self.entryText.selection_get())

	# wrapper for exit function to close rename window first if its open
	def escButton(self, e: Event = None) -> None:
		if self.canvas.itemcget(self.inp,'state') == 'normal':
			self.hideRenameWindow()
			return
		self.exit()

	# properly exit program
	def exit(self, e: Event = None) -> None:
		self.canvas.delete(self.text)
		self.app.quit()
		self.app.destroy()
		exit(0)

	# START BUTTON FUNCTIONS
	def hover(self, id: str, img: ImageTk.PhotoImage) -> None:
		self.canvas.itemconfig(id, image=img)

	def removeHoverDrop(self, e: Event = None) -> None:
		self.canvas.itemconfig(self.dbox, image=self.upb if self.dropDown else self.dropb)

	def hoverOnDrop(self, e: Event = None) -> None:
		self.canvas.itemconfig(self.dbox, image=self.hoverUp if self.dropDown else self.hoverDrop)

	# delete image
	def trashFile(self, e: Event = None) -> None:
		self.clearGif()
		send2trash(os.path.abspath(self.fullname))  # had errors in windows without abspath
		self.hideRenameWindow()
		self.removeAndMove()

	# opens tkinter entry to accept user input
	def renameWindow(self, e: Event = None) -> None:
		if self.canvas.itemcget("topb",'state') == 'hidden':
			self.showWrapper()
		if self.canvas.itemcget(self.inp,'state') == 'hidden':
			self.canvas.itemconfig(self.inp, state='normal')
			self.canvas.coords(self.inp, self.renameWindowLocation+40, 4)
			self.entryText.focus()
			return
		self.hideRenameWindow()

	def FileRenameCleanUp(self, newname: str) -> None:
		newnameObj = self.ImagePath(newname)
		self.files.insert(self.binarySearch(newnameObj.name), newnameObj)
		self.hideRenameWindow()
		self.imageLoaderSafe()
		self.updateTop()

	# asks os to rename file and changes position in list to new location
	def performOSrename(self, newname: str, newPath: str) -> None:
		if os.path.isfile(newPath) or os.path.isdir(newPath):
			raise FileExistsError()
		
		self.temp.close()  # needs to be closed to rename, gif in the middle of loading wouldn't be closed
		os.rename(self.fullname, newPath)
		self.removeImg()
		self.FileRenameCleanUp(newname)

	# returns bool of successful conversion
	def convertFiletype(self, newname: str, newPath: str, imageExtension: str) -> bool:
		if os.path.isfile(newPath) or os.path.isdir(newPath):
			raise FileExistsError()
		
		with open(self.fullname, mode='rb') as fp:
			with Image.open(fp) as temp_img:
				# refuse to convert animations for now
				if(getattr(temp_img, 'n_frames', 1) > 1):
					return False
				
				match imageExtension:
					case '.webp':
						temp_img.save(newPath, 'WebP', quality=100, method=6)
					case '.png':
						temp_img.save(newPath, 'PNG', optimize=True)
					case '.bmp':
						temp_img.save(newPath, 'BMP')
					case '.jpg'|'.jpeg'|'.jif'|'.jfif'|'.jpe':
						if self.files[self.curInd].name[0] == 'j':
							return False
						temp_img.save(newPath, 'JPEG', optimize=True, quality=100)
					case _:
						return False
					
				fp.flush()
			
		if askyesno("Confirm deletion", f"Converted file to {imageExtension}, delete old file?"):
			self.trashFile()
		self.FileRenameCleanUp(newname)
		return True
				

	# trys to rename or convert current file after new name input
	def tryRenameFile(self, e: Event = None) -> None:
		if self.canvas.itemcget(self.inp,'state') == 'hidden': return
		# make a new name removing illegal char for current OS
		newname = sub(self.illegalChar, "", self.entryText.get().strip())  # technically windows allows spaces at end of name but thats a bit silly

		imageExtension = newname[newname.rfind('.', -5):]

		# if valid, try convert
		# else use old extension and rename
		try:
			if imageExtension != self.files[self.curInd].suffix:
				if imageExtension in self.VALID_FILE_TYPES and self.convertFiletype(newname, f'{self.dir}{newname}', imageExtension):
					return
				newname += self.files[self.curInd].suffix
			self.performOSrename(newname, f'{self.dir}{newname}')
		except Exception as e:
			print(e)
			self.entryText.config(bg='#e6505f')  # flash red to tell user can't rename
			self.app.after(400, lambda : self.entryText.config(bg='white'))
		
	# minimizes app
	def minimize(self, e: Event) -> None:
		self.needRedraw = True
		self.app.iconify()

	# START MAIN IMAGE FUNCTIONS
	def resizeImg(self, interpolation: int, wh: tuple[int, int]) -> ImageTk.PhotoImage:
		# simplejpeg is faster way of decoding to numpy array
		if self.temp.format == 'JPEG':
			with open(self.fullname, "rb") as im:
				return ImageTk.PhotoImage(Image.fromarray(cv2.resize(simplejpeg.decode_jpeg(im.read()), wh, interpolation=interpolation)))
		return ImageTk.PhotoImage(Image.fromarray(cv2.resize(asarray(self.temp if self.temp.mode != 'P' else self.temp.convert('RGB'), order='C'), wh, interpolation=interpolation)))
	
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
		self.fullname = f'{self.dir}{self.files[self.curInd].name}'
		try:
			self.temp = Image.open(self.fullname) # open even if in cache to interrupt if user deleted it outside of program
		except(FileNotFoundError, UnidentifiedImageError):
			self.removeAndMove()
			return
		self.bitSize: int = os.path.getsize(self.fullname)
		close: bool = True
		data: self.cached = self.cache.get(curPath.name, None)
		if data is not None and self.bitSize == data.bits: # was cached
			self.trueWidth, self.trueHeight, self.trueSize, self.conImg = data.tw, data.th, data.ts, data.im
		else:
			self.trueWidth, self.trueHeight = self.temp.size
			intSize: int = self.bitSize>>10
			self.trueSize = f"{round(intSize/10.24)/100}mb" if intSize > 999 else f"{intSize}kb"
			wh = self.dimensionFinder()
			frames: int = getattr(self.temp, 'n_frames', 1)
			interpolation: int = cv2.INTER_AREA if self.trueHeight > self.apph else cv2.INTER_CUBIC
			self.conImg = self.resizeImg(interpolation, wh)
			if(frames > 1):  # any non-png animated file, animated png don't work in tkinter it seems
				self.gifFrames = [None] * frames
				self.gifFrames[0] = self.conImg
				Thread(target=self.loadFrame, args=(1, wh, curPath.name, interpolation), daemon=True).start()
				# find animation frame speed
				try:
					speed = int(self.temp.info['duration'] * self.GIFSPEED)
					if speed < 2: speed = self.DEFAULTSPEED
				except(KeyError, AttributeError):
					speed = self.DEFAULTSPEED
				
				self.gifId = self.app.after(speed+20, self.animate, 1, speed, speed+10)
				close = False  # keep open since this is an animation and we need to wait thead to load frames
			else:  # any image thats not cached or animated
				# This cv2 resize is faster than PIL, but convert from P to rgb then resize is slower HOWEVER PIL resize for P mode images looks very bad so still use cv2
				self.cache[curPath.name] = self.cached(self.trueWidth, self.trueHeight, self.trueSize, self.conImg, self.bitSize)
		self.canvas.itemconfig(self.drawnImage, image=self.conImg)
		self.app.title(curPath.name)
		if close: self.temp.close()  # closes in clearGIF function or at end of loading frames if animated, closes here otherwise
		

	# wrapper for image loader that clears gifs before loading new image
	def imageLoaderSafe(self) -> None:
		self.clearGif()
		self.imageLoader()

	def showTopbar(self) -> None:
		self.canvas.itemconfig("topb", state='normal')
		self.updateTop()

	# wraps showTopbar and sets flag that topbar has been drawn
	def showWrapper(self, e: Event = None) -> None:
		self.drawtop = True
		self.showTopbar()

	def hideTopbar(self, e: Event = None) -> None:
		self.canvas.itemconfig("topb", state='hidden')
		self.hideRenameWindow()

	# wraps hideTopbar and sets flag that topbar has not been drawn
	def hideWrapper(self, e: Event = None) -> None:
		self.drawtop = False
		self.app.focus()
		self.hideTopbar()

	# skip clicks to menu, draws menu if not present
	def clickHandler(self, e: Event) -> None:
		self.drawtop = not self.drawtop
		self.app.focus()
		if self.drawtop: 
			self.showTopbar()
		else: 
			self.hideTopbar()

	def removeImg(self) -> None:
		# delete image from files array and from cache if present
		self.cache.pop(self.files.pop(self.curInd).name, None)

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
		self.renameWindowLocation = self.canvas.bbox(self.text)[2]
		self.canvas.coords(self.renameButton, self.renameWindowLocation, 0)
		self.createDropbar() if self.dropDown else self.canvas.itemconfig(self.infod, state='hidden')
	# END MAIN IMAGE FUNCTIONS

	# START GIF FUNCTIONS
	''' gifFrame: int representing current frame
		orgSpeed: speed in ms until next frame
		buffer: orgSpeed with delay, used if gif is taking too long to load -> add additional time between trying to dispaly next frame
	'''
	def animate(self, gifFrame: int, orgSpeed: int, buffer: int) -> None:
		gifFrame += 1
		if gifFrame >= len(self.gifFrames): gifFrame = 0

		speed = orgSpeed  # speed after which to try and show next frame
		img = self.gifFrames[gifFrame]
		# tried to show next frame before it is loaded, reset to current frame and try again after delay
		if img is None:
			speed = buffer
			gifFrame -= 1
			buffer += 10
		else:
			self.canvas.itemconfig(self.drawnImage, image=img)	

		self.gifId = self.app.after(speed, self.animate, gifFrame, orgSpeed, buffer)

	def loadFrame(self, gifFrame: int, wh: tuple[int, int], name: str, interpolation: int) -> None:
		# move function would have already closed old gif, so if new gif on screen, don't keep loading previous gif
		if name != self.files[self.curInd].name: return
		try:
			self.temp.seek(gifFrame)
			self.gifFrames[gifFrame] = self.resizeImg(interpolation, wh)
			self.loadFrame(gifFrame+1, wh, name, interpolation)
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
	def toggleDrop(self, e: Event) -> None:
		self.dropDown = not self.dropDown
		self.hoverOnDrop()
		self.createDropbar() if self.dropDown else self.canvas.itemconfig(self.infod, state='hidden')
		
	def createDropbar(self) -> None:
		dimText: str = f"Pixels: {self.trueWidth}x{self.trueHeight}"
		draw = ImageDraw.Draw(Image.new('RGBA', (int(ImageDraw.ImageDraw.font.getlength(dimText))+20, self.DROPDOWNHEIGHT), (40, 40, 40, 170)))  # copy plain window and draw on it
		draw.text((10, 25), dimText, fill="white")
		draw.text((10, 60), f"Size: {self.trueSize}", fill="white")
		self.dropImage = ImageTk.PhotoImage(draw._image)
		self.canvas.itemconfig(self.infod, image=self.dropImage, state='normal')
	# END DROPDOWN FUNCTIONS

	# find index of image in the sorted list of all images in directory
	# pth: name of image file to find
	def binarySearch(self, pth: str) -> int:
		low, high = 0, len(self.files)-1
		while low <= high:
			mid = (low+high)>>1
			cur = self.files[mid].name
			if pth == cur: return mid
			if utilHelper.myCmpW(pth, cur): high = mid-1
			else: low = mid+1
		return low

if __name__ == "__main__":
	DEBUG: bool = False
	if len(argv) > 1:
		viewer(argv[1])
	elif DEBUG:
		from time import perf_counter_ns, sleep # DEBUG
		viewer(r"C:\Users\jimde\OneDrive\Pictures\myself.jpg") # DEBUG
	else:
		print('An Image Viewer written in Python\nRun with \'python -m viewer "C:/path/to/an/image"\' or convert to an exe and select "open with" on your image')
