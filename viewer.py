# python -m nuitka --windows-disable-console --windows-icon-from-ico="C:\PythonCode\Viewer\icon\icon.ico" viewer.py
# pyinstaller is very slow, please use nuitka if you plan to compile it yourself
from sys import argv  # std
from tkinter import Tk, Canvas, Entry  # std
from PIL import Image, ImageTk, ImageDraw, ImageFont, UnidentifiedImageError  # 9.1.0
from os import path, stat, rename  # std
from send2trash import send2trash  # 1.8.0
from pathlib import Path  # std
from ctypes import windll  # std
from cython import int as cint  # 0.29.28
from cython import struct, cfunc, bint  # 0.29.28
from natsort import os_sorted  # 8.1.0
#import time

# constants
DEBUG: bint = False
SPACE: cint = 32
LINECOL: tuple = (170, 170, 170)
ICONCOL: tuple = (100, 104, 102)
ICONHOV: tuple = (95, 92, 88)
TOPCOL: tuple = (60, 60, 60, 170)
FILETYPE: set = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".jfif"}
DROPDOWNWIDTH: cint = 190
DROPDOWNHEIGHT: cint = 110
FONT: str = 'arial 11'
cached = struct(w=cint, h=cint, tw=cint, th=cint, ts=str, im=ImageTk)  # struct for holding cached data

#  fits width and height to tkinter window
@cfunc
def dimensionFinder(w: cint, h: cint, dimw: cint, dimh: cint) -> tuple[cint, cint]:
    ''' w,h are width and height of image before resize
        dimw, dimh are the screen's dimentions 
    '''
    width: cint = round(w * (dimh/h))
    #  Size to height of window. If that makes the image too wide, size to width instead
    return (width, dimh) if width <= dimw else (dimw, round(h * (dimw/w)))
    
# loads image path
def imageLoader(path) -> None:
    global image, canvas, cache, app, trueWidth, trueHeight, trueSize, gifFrames, gifId, appw, apph, temp
    
    try:
        temp = Image.open(path)  #  open even if in cache to interrupt if user deleted it outside of program
        w: cint
        h: cint
        if path not in cache:
            trueWidth, trueHeight = temp.size
            intSize: cint = round(stat(path).st_size/1000)
            trueSize = f"{round(intSize/1000, 2)}mb" if intSize > 999 else f"{intSize}kb"
            w, h = dimensionFinder(trueWidth, trueHeight, appw, apph)
            if path.suffix == '.gif':
                try:
                    speed: cint = temp.info['duration']
                    if speed < 2: speed = 100
                except(KeyError, AttributeError):
                    speed: cint = 100
                if not gifFrames:
                    gifFrames = [None] * temp.n_frames
                    gifFrames[0] = ImageTk.PhotoImage(temp.resize((w, h), Image.Resampling.HAMMING))

                image = gifFrames[0]
                gifId = app.after(speed, animate, 0, w, h, path, speed, temp)
                w, h = (appw-w) >> 1, (apph-h) >> 1
            else:
                image = ImageTk.PhotoImage(temp.resize((w, h), Image.Resampling.LANCZOS))
                w, h = (appw-w) >> 1, (apph-h) >> 1
                cache[path] = cached(w=w, h=h, tw=trueWidth, th=trueHeight, ts=trueSize, im=image)
        else:
            data = cache[path]
            trueWidth, trueHeight, trueSize, image, w, h = data.tw, data.th, data.ts, data.im, data.w, data.h
        canvas.itemconfig('drawnImage', image=image)
        canvas.coords('drawnImage', w, h)
        if path.suffix != '.gif': temp.close()
        app.title(files[curInd].name)
    except(FileNotFoundError, UnidentifiedImageError):
        removeAndMove()

# used for gif files
def animate(gifFrame: cint, w: cint, h: cint, path, speed: cint, temp) -> None:
    global gifFrames, gifId
    gifFrame = gifFrame+1 
    if gifFrame >= len(gifFrames): gifFrame = 0
    img = gifFrames[gifFrame]
    if img is None:
        img = ImageTk.PhotoImage(temp.resize((w, h), Image.Resampling.HAMMING))
        gifFrames[gifFrame] = img
        temp.seek(gifFrame)
        if gifFrame == len(gifFrames)-1: temp.close()
    canvas.itemconfig('drawnImage', image=img)
    if len(gifFrames) > 1: gifId = app.after(speed, animate, gifFrame, w, h, path, speed, temp)   


def loadFrame(frameNum: cint, temp, w: cint, h: cint):
    gifFrames[gifFrame] = ImageTk.PhotoImage(temp.resize((w, h), Image.Resampling.HAMMING))
    temp.seek(gifFrame)
    if gifFrame == len(gifFrames)-1: temp.close()
    

def hover(id, img) -> None:
    global canvas
    canvas.itemconfig(id, image=img)

def removeHoverDrop(event=None) -> None:
    global canvas, dropDown, upb, dropb, d
    switch = upb if dropDown else dropb
    canvas.itemconfig(d, image=switch)

def hoverOnDrop(event=None) -> None:
    global canvas, dropDown, hoverUp, hoverDrop, d
    switch = hoverUp if dropDown else hoverDrop
    canvas.itemconfig(d, image=switch)

# switches if dropdown is drawn or not
def toggleDrop(event=None) -> None:
    global dropDown, canvas, hoverUp, infod
    dropDown = not dropDown
    hoverOnDrop()
    if dropDown: createDropbar()
    else: canvas.itemconfig(infod, state='hidden')
    
def createDropbar() -> None:
    global canvas, dropbar, dropImage, fnt, trueWidth, trueHeight, trueSize, infod
    draw = ImageDraw.Draw(dropbar.copy())  # copy plain window and draw on it
    draw.text((10, 25), f"Pixels: {trueWidth}x{trueHeight}", font=fnt, fill="white")
    draw.text((10, 60), f"Size: {trueSize}", font=fnt, fill="white")
    dropImage = ImageTk.PhotoImage(draw._image)
    canvas.itemconfig(infod, image=dropImage, state='normal')

# minimizes app
def minimize(event) -> None:
    global app
    app.iconify()

# closes app    
def exitApp(event) -> None:
    global app
    app.quit()

# move between images when mouse scolls
def scrollhandler(event) -> None:
    global curInd, files, app, entryText, drawtop
    if entryText is not None:
        deleteRenameBox()
    clearGif()
    if event.delta > 0:
        curInd = len(files)-1 if curInd == 0 else curInd-1
    else:
        curInd = 0 if curInd == len(files)-1 else curInd+1
    imageLoader(files[curInd])
    if drawtop: updateTop()

# clear cached images if window gets resized
def resizeHandler(event) -> None:
    global cache, app, appw, apph
    cache.clear()
    app.update()
    appw, apph = app.winfo_width(), app.winfo_height()

# delete image
def trashFile(event) -> None:
    global curInd, files, image
    send2trash(files[curInd])
    clearGif()
    removeAndMove()

# remove from list and move to next image
def removeAndMove() -> None:
    global files, curInd, cache
    if files[curInd] in cache:
        del cache[files[curInd]]
    del files[curInd]
    if curInd >= len(files):
        curInd = len(files)-1
    imageLoader(files[curInd])

def updateTop() -> None:
    global canvas, loc, files, curInd, dropDown, text
    canvas.itemconfig(text, text=files[curInd].name)
    loc = canvas.bbox(text)[2]
    canvas.coords('renamer', loc, 0)
    if dropDown: createDropbar()

# skip clicks to menu, draws menu if not present
def clickHandler(event) -> None:
    global drawtop, dropDown, appw, canvas
    if drawtop and (event.y <= SPACE or (dropDown and event.x > appw-DROPDOWNWIDTH and event.y < SPACE+DROPDOWNHEIGHT)):
        return
    drawtop = not drawtop
    deleteRenameBox()
    state = 'normal' if drawtop else 'hidden'
    canvas.itemconfig("topb", state=state)
    if drawtop: updateTop()

# sometimes (inconsistently) goes blank when opening from taskbar. This redraws to prevent that
def drawWrapper(event=None) -> None:
    global curInd, files
    imageLoader(files[curInd])

# opens tkinter entry to accept user input
def renameWindow(event) -> None:
    global canvas, app, entryText, loc, savedText
    if entryText is None:
        entryText = Entry(app, font=FONT)
        entryText.insert('end', savedText)
        entryText.bind('<Return>', renameFile)
        canvas.itemconfig("userinput", window=entryText, state='normal')
        canvas.coords("userinput", loc+40, 4)
    else: deleteRenameBox()

    
# asks os to rename file and changes position in list to new location
def renameFile(event) -> None:
    global entryText, files, curInd
    if entryText is None: return
    newname = f'{files[curInd].parent}/{entryText.get().strip()}{files[curInd].suffix}'
    try:
        rename(files[curInd], newname) 
        newname = Path(newname)
        del files[curInd]
        files.append(newname)
        files = os_sorted(files)  # less efficent than insertion, but os sorting not same as normal sorting...
        deleteRenameBox()
        clearGif()
        imageLoader(files[curInd])
        updateTop()
    except Exception as e:
        entryText.config(bg='#e6505f')  # flash red to tell user can't rename
        app.after(400, revert)

def revert() -> None:
    global entryText
    if entryText is not None: entryText.config(bg="White")

def deleteRenameBox() -> None:
    global canvas, entryText, savedText
    if entryText is None: return
    savedText = entryText.get()  # comment this to remove text saving in rename window
    canvas.itemconfig("userinput", state='hidden')
    entryText.destroy()
    entryText = None

def clearGif() -> None:
    global gifFrames, gifFrame, gifId, app, temp
    if gifId is None: return
    app.after_cancel(gifId)
    gifId = None
    gifFrames.clear()
    temp.close()

def refresh() -> None:
    global cache, files, dir, curInd, image
    cache.clear()
    files = os_sorted([p for p in dir.glob("*") if p.suffix in FILETYPE])
    try:
        curInd = files.index(image)
    except ValueError:
        curInd = 0
    drawWrapper()

if __name__ == "__main__":
    if len(argv) > 1 or DEBUG:
        image = Path(r"C:\PythonCode\test.jpg") if DEBUG else Path(argv[1])
        if image.suffix not in FILETYPE: exit()
        windll.shcore.SetProcessDpiAwareness(1)
        # UI varaibles
        drawtop: bint = False  # if drawn
        dropDown: bint = False  # if drawn
        entryText = dropImage = None  # acts as refrences to items
        savedText = ''
        fnt = ImageFont.truetype("arial.ttf", 22)  # font for drawing on images
        # data on current image
        trueWidth: cint = 0 
        trueHeight: cint = 0
        trueSize: str = ''
        # gif support
        loc: cint = 0  # location of rename button
        gifFrames: list = []  # None if current image not gif, else id for animation loop
        gifId = None  # id for gif animiation
        # main stuff
        app = Tk()
        cache: dict = dict()  # cache rendered images
        canvas = Canvas(app, bg='black', highlightthickness=0)
        canvas.pack(anchor='nw', fill='both', expand=1)
        canvas.create_image(0, 0, anchor='nw', tag='drawnImage')  # main image to be replaced
        app.attributes('-fullscreen', True)
        app.state('zoomed')
        app.update()  # updates winfo width and height to the current size, this is necessary
        appw: cint = app.winfo_width()
        apph: cint = app.winfo_height()

        # make assests for menu
        topbar = ImageTk.PhotoImage(Image.new('RGBA', (app.winfo_width(), SPACE), TOPCOL))
        dropbar = Image.new('RGBA', (DROPDOWNWIDTH, DROPDOWNHEIGHT), (40, 40, 40, 170))
        exitb = ImageTk.PhotoImage(Image.new('RGB', (SPACE, SPACE), (190, 40, 40)))
        hoveredExit = Image.new('RGB', (SPACE, SPACE), (180, 25, 20))
        draw: ImageDraw = ImageDraw.Draw(hoveredExit) 
        draw.line((6, 6, 26, 26), width=2, fill=LINECOL)
        draw.line((6, 26, 26, 6), width=2, fill=LINECOL)
        hoveredExit = ImageTk.PhotoImage(draw._image)
        minib = Image.new('RGB', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(minib) 
        draw.line((6, 24, 24, 24), width=2, fill=LINECOL)
        minib = ImageTk.PhotoImage(draw._image)
        hoveredMini = Image.new('RGB', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoveredMini) 
        draw.line((6, 24, 24, 24), width=2, fill=LINECOL)
        hoveredMini = ImageTk.PhotoImage(draw._image)
        trashb = Image.new('RGB', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(trashb) 
        draw.line((9, 9, 9, 22), width=2, fill=LINECOL)
        draw.line((21, 9, 21, 22), width=2, fill=LINECOL)
        draw.line((9, 22, 21, 22), width=2, fill=LINECOL)
        draw.line((7, 9, 24, 9), width=2, fill=LINECOL)
        draw.line((12, 8, 19, 8), width=3, fill=LINECOL)
        trashb = ImageTk.PhotoImage(draw._image)
        hoverTrash = Image.new('RGB', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoverTrash) 
        draw.line((9, 9, 9, 22), width=2, fill=LINECOL)
        draw.line((21, 9, 21, 22), width=2, fill=LINECOL)
        draw.line((9, 22, 21, 22), width=2, fill=LINECOL)
        draw.line((7, 9, 24, 9), width=2, fill=LINECOL)
        draw.line((12, 8, 19, 8), width=3, fill=LINECOL)
        hoverTrash = ImageTk.PhotoImage(draw._image)
        dropb = Image.new('RGB', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(dropb) 
        draw.line((6, 11, 16, 21), width=2, fill=LINECOL)
        draw.line((16, 21, 26, 11), width=2, fill=LINECOL)
        dropb = ImageTk.PhotoImage(draw._image)
        hoverDrop = Image.new('RGB', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoverDrop) 
        draw.line((6, 11, 16, 21), width=2, fill=LINECOL)
        draw.line((16, 21, 26, 11), width=2, fill=LINECOL)
        hoverDrop = ImageTk.PhotoImage(draw._image)
        upb = Image.new('RGB', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(upb) 
        draw.line((6, 21, 16, 11), width=2, fill=LINECOL)
        draw.line((16, 11, 26, 21), width=2, fill=LINECOL)
        draw.line((16, 11, 16, 11), width=1, fill=LINECOL)
        upb = ImageTk.PhotoImage(draw._image)
        hoverUp = Image.new('RGB', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoverUp) 
        draw.line((6, 21, 16, 11), width=2, fill=LINECOL)
        draw.line((16, 11, 26, 21), width=2, fill=LINECOL)
        draw.line((16, 11, 16, 11), width=1, fill=LINECOL)
        hoverUp = ImageTk.PhotoImage(draw._image)
        renameb = Image.new('RGB', (SPACE, SPACE), (0,0,0,0))
        draw = ImageDraw.Draw(renameb) 
        draw.rectangle((7, 10, 25, 22), width=1, fill=None, outline=LINECOL)
        draw.line((7, 16, 16, 16), width=3, fill=LINECOL)
        draw.line((16, 8, 16, 24), width=2, fill=LINECOL)
        renameb = ImageTk.PhotoImage(draw._image)
        hoverRename = Image.new('RGB', (SPACE, SPACE), (0,0,0,0))
        draw = ImageDraw.Draw(hoverRename) 
        draw.rectangle((4, 5, 28, 27), width=1, fill=ICONHOV)
        draw.rectangle((7, 10, 25, 22), width=1, fill=None, outline=LINECOL)
        draw.line((7, 16, 16, 16), width=3, fill=LINECOL)
        draw.line((16, 8, 16, 24), width=2, fill=LINECOL)
        hoverRename = ImageTk.PhotoImage(draw._image)
        
        # events based on input
        app.bind("<MouseWheel>", scrollhandler)
        canvas.bind("<Button-1>", clickHandler)
        app.bind("<Configure>", resizeHandler)
        #app.bind("<FocusIn>", lambda e: print('focus!'))

        dir = Path(f'{path.dirname(image)}/')
        files: list = os_sorted([p for p in dir.glob("*") if p.suffix in FILETYPE])
        curInd: cint = files.index(image)
        # topbar assests
        canvas.create_image(0, 0, image=topbar, anchor='nw', tag="topb")
        text = canvas.create_text(36, 5, text='', fill="white", anchor='nw', font=FONT, tag="topb")
        r = canvas.create_image(0, 0, image=renameb, anchor='nw', tag='topb')
        b = canvas.create_image(appw-SPACE, 0, image=exitb, anchor='nw', tag='topb')
        b2 = canvas.create_image(appw-SPACE-SPACE, 0, image=minib, anchor='nw', tag='topb')
        t = canvas.create_image(0, 0, image=trashb, anchor='nw', tag='topb')
        canvas.tag_bind(b, '<Button-1>', exitApp)
        canvas.tag_bind(b2,'<Button-1>', minimize)
        canvas.tag_bind(t, '<Button-1>', trashFile)
        canvas.tag_bind(r, '<Button-1>', renameWindow)
        canvas.tag_bind(b, '<Enter>', lambda e: hover(id=b, img=hoveredExit))
        canvas.tag_bind(b, '<Leave>', lambda e: hover(id=b, img=exitb))
        canvas.tag_bind(b2,'<Enter>', lambda e: hover(id=b2, img=hoveredMini))
        canvas.tag_bind(b2,'<Leave>', lambda e: hover(id=b2, img=minib))
        canvas.tag_bind(t, '<Enter>', lambda e: hover(id=t, img=hoverTrash))
        canvas.tag_bind(t, '<Leave>', lambda e: hover(id=t, img=trashb))
        canvas.tag_bind(r, '<Enter>', lambda e: hover(id=r, img=hoverRename))
        canvas.tag_bind(r, '<Leave>', lambda e: hover(id=r, img=renameb))
        if dropDown:
            d = canvas.create_image(appw-(SPACE*3), 0, image=upb, anchor='nw', tag='topb')
            createDropbar()
        else:
            d = canvas.create_image(appw-(SPACE*3), 0, image=dropb, anchor='nw', tag='topb') 
        canvas.create_window(0, 0, width=200, height=24, anchor='nw', tag="userinput")  # rename window
        canvas.tag_bind(d, '<Button-1>', toggleDrop)
        canvas.tag_bind(d, '<Enter>', hoverOnDrop)
        canvas.tag_bind(d, '<Leave>', removeHoverDrop)
        canvas.itemconfig("topb", state='hidden')
        canvas.itemconfig(text, state='hidden')
        canvas.itemconfig(r, state='hidden')
        canvas.itemconfig(b, state='hidden')
        canvas.itemconfig(b2, state='hidden')
        canvas.itemconfig(t, state='hidden')
        canvas.itemconfig(d, state='hidden')
        canvas.itemconfig("userinput", state='hidden')
        # dropbox
        infod = canvas.create_image(appw-DROPDOWNWIDTH, SPACE, anchor='nw', tag="topb")

        imageLoader(files[curInd])
        
        app.mainloop()
