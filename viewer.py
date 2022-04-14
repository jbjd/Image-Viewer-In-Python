# python -m nuitka --windows-disable-console --include-plugin-directory=C:\PythonCode\Viewer\gifraw --windows-icon-from-ico="C:\PythonCode\Viewer\icon\icon.ico" viewer.py
# pyinstaller is very slow, please use nuitka if you plan to compile it yourself
from sys import argv
from tkinter import Tk, Canvas, Entry
from PIL import Image, ImageTk, ImageDraw, ImageFont, UnidentifiedImageError
from os import path, stat, rename
from send2trash import send2trash
from pathlib import Path
from ctypes import windll
from cython import int as cint
from cython import struct, cfunc, bint
from natsort import os_sorted
from io import BytesIO
from gifraw import GifRaw
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
    height: cint = dimh
    width: cint = int(w * (height/h))
    #  Size to height of window. If that makes the image too wide, size to width instead
    return (width, height) if width <= dimw else (dimw, int(h * (dimw/w)))
    
# loads image path
def imageLoader(path) -> None:
    global image, canvas, cache, app, drawtop, trueWidth, trueHeight, trueSize, gifFrames, gifFrame, gifId, gifRaw, gifCache  # variables for drawing
    if not path: return

    try:
        temp = Image.open(path)
        w: cint
        h: cint
        if path.suffix == '.gif':
            trueWidth, trueHeight = temp.size
            intSize: cint = round(stat(path).st_size/1000)
            trueSize = str(round(intSize/1000, 2))+"mb" if intSize > 999 else str(intSize)+"kb"
            w, h = dimensionFinder(trueWidth, trueHeight, app.winfo_width(), app.winfo_height())
            if path not in gifCache:
                if not gifFrames:
                    gifRaw = GifRaw(str(path))
                    gifRaw.make_raw_image_list()
                    gifFrames = [None] * gifRaw.frames
                    createFrame(0, w, h, path)
            else:
                gifFrames = gifCache[path].copy()
            image, speed = gifFrames[gifFrame]
            if speed < 10: speed = 100
            if gifId is None: gifId = app.after(speed, animate, w, h, path)
            w, h = int((app.winfo_width()-w)/2), int((app.winfo_height()-h)/2)
        elif path not in cache:
            trueWidth, trueHeight = temp.size
            intSize: cint = round(stat(path).st_size/1000)
            trueSize = str(round(intSize/1000, 2))+"mb" if intSize > 999 else str(intSize)+"kb"
            w, h = dimensionFinder(trueWidth, trueHeight, app.winfo_width(), app.winfo_height())  # get resized dimensions for fullscreen view
            
            image = temp.resize((w, h), Image.ANTIALIAS)
            image = ImageTk.PhotoImage(image)
            w, h = int((app.winfo_width()-w)/2), int((app.winfo_height()-h)/2)
            
            cache[path] = cached(w=w, h=h, tw=trueWidth, th=trueHeight, ts=trueSize, im=image)
        else:
            data = cache[path]
            trueWidth, trueHeight, trueSize, image = data.tw, data.th, data.ts, data.im
            w, h = data.w, data.h
        canvas.delete("all")
        canvas.create_image(w, h, image=image, anchor='nw', tag='drawnImage')
        temp.close()
        if drawtop:
            drawTop()
    except(FileNotFoundError, UnidentifiedImageError):
        removeAndMove()

# used for gif files
def animate(w, h, path):
    global gifFrames, gifId, gifFrame
    gifFrame += 1
    if gifFrame >= len(gifFrames): gifFrame = 0
    if gifFrames[gifFrame] == None: createFrame(gifFrame, w, h, path)
    img, speed = gifFrames[gifFrame]
    if speed < 10: speed = 100
    canvas.itemconfig('drawnImage', image=img)
    if len(gifFrames) > 1: gifId = app.after(speed, animate, w, h, path)

def createFrame(idx, w, h, path):
    global gifRaw, gifFrame, saved_img, gifCache
    
    outimg = Image.open(BytesIO(gifRaw.raw_img_list[idx])).convert("RGBA")
       
    if idx == 0:
        saved_img = outimg
    else:
        outimg.point(lambda p: p > 255 and 255)
        saved_img.alpha_composite(outimg)
    try:
        gifFrames[idx] = (ImageTk.PhotoImage(saved_img.resize((w, h), Image.ANTIALIAS)), outimg.info['duration'])
    except KeyError:
        gifFrames[idx] = (ImageTk.PhotoImage(saved_img.resize((w, h), Image.ANTIALIAS)), 100)
    if idx+1 == len(gifFrames) and len(gifCache) < 16: gifCache[path] =  gifFrames.copy()


# handles hovering icons
def hoverExit(id, img) -> None:
    global canvas
    canvas.itemconfig(id, image=img)

def hover(id, img) -> None:
    global canvas
    canvas.itemconfig(id, image=img)

# switches if dropdown is drawn or not
def toggleDrop(event) -> None:
    global dropDown, canvas, hoverUp
    dropDown = not dropDown
    hover('dropper', hoverUp)
    if dropDown: createDropbar()
    else: canvas.delete("dropped")

def drawTop() -> None:
    global canvas, loc, files, curInd
    canvas.create_image(0, 0, image=topbar, anchor='nw')
    text = canvas.create_text(36, 5, text=files[curInd].name, fill="white", anchor='nw', font=FONT, tag="text")
    loc = canvas.bbox(text)[2]
    r = canvas.create_image(loc, 0, image=renameb, anchor='nw', tag='renamer')
    b = canvas.create_image(app.winfo_width()-SPACE, 0, image=exitb, anchor='nw', tag='exiter')
    b2 = canvas.create_image(app.winfo_width()-SPACE-SPACE, 0, image=minib, anchor='nw', tag='minimizer')
    t = canvas.create_image(0, 0, image=trashb, anchor='nw', tag='trasher')
    canvas.tag_bind(b, '<Button-1>', exitApp)
    canvas.tag_bind(b2,'<Button-1>', minimize)
    canvas.tag_bind(t, '<Button-1>', trashFile)
    canvas.tag_bind(r, '<Button-1>', renameWindow)
    canvas.tag_bind(b, '<Enter>', lambda e: hover(id="exiter", img=hoveredExit))
    canvas.tag_bind(b, '<Leave>', lambda e: hover(id="exiter", img=exitb))
    canvas.tag_bind(b2,'<Enter>', lambda e: hover(id="minimizer", img=hoveredMini))
    canvas.tag_bind(b2,'<Leave>', lambda e: hover(id="minimizer", img=minib))
    canvas.tag_bind(t, '<Enter>', lambda e: hover(id="trasher", img=hoverTrash))
    canvas.tag_bind(t, '<Leave>', lambda e: hover(id="trasher", img=trashb))
    canvas.tag_bind(r, '<Enter>', lambda e: hover(id="renamer", img=hoverRename))
    canvas.tag_bind(r, '<Leave>', lambda e: hover(id="renamer", img=renameb))
    if dropDown:
        d = canvas.create_image(app.winfo_width()-(SPACE*3), 0, image=upb, anchor='nw', tag='dropper')
        createDropbar()
        dropimg, hoverimg = upb, hoverUp
    else:
        d = canvas.create_image(app.winfo_width()-(SPACE*3), 0, image=dropb, anchor='nw', tag='dropper')
        dropimg, hoverimg = dropb, hoverDrop
    canvas.tag_bind(d, '<Button-1>', toggleDrop)
    canvas.tag_bind(d, '<Enter>', lambda e: hover(id="dropper", img=hoverimg))
    canvas.tag_bind(d, '<Leave>', lambda e: hover(id="dropper", img=dropimg))
    
def createDropbar() -> None:
    global canvas, dropbar, dropImage, fnt, trueWidth, trueHeight, trueSize
    draw = ImageDraw.Draw(dropbar.copy())
    draw.text((10, 25), f"Pixels: {trueWidth}x{trueHeight}", font=fnt, fill="white")
    draw.text((10, 60), f"Size: {trueSize}", font=fnt, fill="white")
    dropImage = ImageTk.PhotoImage(draw._image)
    canvas.create_image(app.winfo_width()-DROPDOWNWIDTH, SPACE, image=dropImage, anchor='nw', tag="dropped")

# minimizes app
def minimize(event) -> None:
    global app, gifId
    if gifId is not None: 
        app.after_cancel(gifId)
        gifId = None
    app.iconify()

# closes app    
def exitApp(event) -> None:
    global app
    app.quit()

# move between images when mouse scolls
def scrollhandler(event) -> None:
    global curInd, files, app, entryText
    if entryText is not None:
        deleteRenameBox()
    clearGif()
    if event.delta > 0:
        curInd = len(files)-1 if curInd == 0 else curInd-1
        imageLoader(files[curInd])
    else:
        curInd = 0 if curInd == len(files)-1 else curInd+1
        imageLoader(files[curInd])

# clear cached images if window gets resized
def resizeHandler(event) -> None:
    global cache, gifCache
    cache.clear()
    gifCache.clear()

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

# skip clicks to menu, draws menu if not present
def clickHandler(event) -> None:
    global curInd, files, drawtop, dropDown, app
    if drawtop and (event.y <= SPACE or (dropDown and event.x > app.winfo_width()-DROPDOWNWIDTH and event.y < SPACE+DROPDOWNHEIGHT)): 
        return
    drawtop = not drawtop
    deleteRenameBox()
    if drawtop: drawTop()
    else: imageLoader(files[curInd])

# sometimes (inconsistently) goes blank when opening from taskbar. This redraws to prevent that
def drawWrapper(event) -> None:
    global curInd, files
    imageLoader(files[curInd])

# opens tkinter entry to accept user input
def renameWindow(event) -> None:
    global canvas, app, entryText, loc
    entryText = Entry(app, font=FONT)
    entryText.insert('end', savedText)
    entryText.bind('<Return>', renameFile)
    canvas.create_window(loc+40, 4, width=200, height=24, window=entryText, anchor='nw', tag="userinput")
    
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
    except Exception as e:
        entryText.config(bg='#e6505f')  # flash red to tell user can't rename
        app.after(400, revert)

def revert() -> None:
    global entryText
    entryText.config(bg="White")

def deleteRenameBox() -> None:
    global canvas, entryText, savedText
    if entryText is None: return
    savedText = entryText.get()  # comment this to remove text saving in rename window
    canvas.delete('userinput')
    entryText.destroy()
    entryText = None

def clearGif() -> None:
    global gifFrames, gifFrame, gifRaw, gifId, app
    if gifId is None: return
    app.after_cancel(gifId)
    gifId = gifRaw = None
    gifFrames.clear()
    gifFrame = 0 

def refresh() -> None:
    global cache, gifCache, files, dir, curInd, image
    cache.clear()
    gifCache.clear()
    files = os_sorted([p for p in dir.glob("*") if p.suffix in FILETYPE])
    try:
        curInd = files.index(image)
    except  ValueError:
        curInd = 0
    drawWrapper()

if __name__ == "__main__":
    if len(argv) > 1 or DEBUG:
        image = Path(r"C:\Pictures\grafu.gif") if DEBUG else Path(argv[1])
        if image.suffix not in FILETYPE: exit()
        windll.shcore.SetProcessDpiAwareness(1)
        # initialize main window + important data
        drawtop: bint = False  # if drawn
        dropDown: bint = False  # if drawn
        entryText = dropImage = None  # acts as refrences to items
        savedText: str = ''
        fnt = ImageFont.truetype("arial.ttf", 22)  # font for drawing on images
        # data on current image
        trueWidth: cint = 0 
        trueHeight: cint = 0
        trueSize: str = ''
        loc: cint = 0  # location of rename button
        gifFrames: list = []  # None if current image not gif, else id for animation loop
        gifId = gifRaw = None  # id for gif animiation
        gifFrame = 0
        gifCache: dict = dict()  # cache rendered frames of a gif
        cache: dict = dict()  # cache rendered images
        app = Tk()
        canvas = Canvas(app, bg='black', highlightthickness=0)
        canvas.pack(anchor='nw', fill='both', expand=1)

        app.attributes('-fullscreen', True)
        app.state('zoomed')
        app.update()  # updates winfo width and height to the current size, this is necessary

        # make assests for menu
        topbar = ImageTk.PhotoImage(Image.new('RGBA', (app.winfo_width(), SPACE), TOPCOL))
        dropbar = Image.new('RGBA', (DROPDOWNWIDTH, DROPDOWNHEIGHT), (40, 40, 40, 170))
        exitb = ImageTk.PhotoImage(Image.new('RGBA', (SPACE, SPACE), (190, 40, 40)))
        hoveredExit = Image.new('RGBA', (SPACE, SPACE), (180, 25, 20))
        draw: ImageDraw = ImageDraw.Draw(hoveredExit) 
        draw.line((6, 6, 26, 26), width=2, fill=LINECOL)
        draw.line((6, 26, 26, 6), width=2, fill=LINECOL)
        hoveredExit = ImageTk.PhotoImage(draw._image)
        minib = Image.new('RGBA', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(minib) 
        draw.line((6, 24, 24, 24), width=2, fill=LINECOL)
        minib = ImageTk.PhotoImage(draw._image)
        hoveredMini = Image.new('RGBA', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoveredMini) 
        draw.line((6, 24, 24, 24), width=2, fill=LINECOL)
        hoveredMini = ImageTk.PhotoImage(draw._image)
        trashb = Image.new('RGBA', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(trashb) 
        draw.line((9, 9, 9, 22), width=2, fill=LINECOL)
        draw.line((21, 9, 21, 22), width=2, fill=LINECOL)
        draw.line((9, 22, 21, 22), width=2, fill=LINECOL)
        draw.line((7, 9, 24, 9), width=2, fill=LINECOL)
        draw.line((12, 8, 19, 8), width=3, fill=LINECOL)
        trashb = ImageTk.PhotoImage(draw._image)
        hoverTrash = Image.new('RGBA', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoverTrash) 
        draw.line((9, 9, 9, 22), width=2, fill=LINECOL)
        draw.line((21, 9, 21, 22), width=2, fill=LINECOL)
        draw.line((9, 22, 21, 22), width=2, fill=LINECOL)
        draw.line((7, 9, 24, 9), width=2, fill=LINECOL)
        draw.line((12, 8, 19, 8), width=3, fill=LINECOL)
        hoverTrash = ImageTk.PhotoImage(draw._image)
        dropb = Image.new('RGBA', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(dropb) 
        draw.line((6, 11, 16, 21), width=2, fill=LINECOL)
        draw.line((16, 21, 26, 11), width=2, fill=LINECOL)
        dropb = ImageTk.PhotoImage(draw._image)
        hoverDrop = Image.new('RGBA', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoverDrop) 
        draw.line((6, 11, 16, 21), width=2, fill=LINECOL)
        draw.line((16, 21, 26, 11), width=2, fill=LINECOL)
        hoverDrop = ImageTk.PhotoImage(draw._image)
        upb = Image.new('RGBA', (SPACE, SPACE), ICONCOL)
        draw = ImageDraw.Draw(upb) 
        draw.line((6, 21, 16, 11), width=2, fill=LINECOL)
        draw.line((16, 11, 26, 21), width=2, fill=LINECOL)
        draw.line((16, 11, 16, 11), width=1, fill=LINECOL)
        upb = ImageTk.PhotoImage(draw._image)
        hoverUp = Image.new('RGBA', (SPACE, SPACE), ICONHOV)
        draw = ImageDraw.Draw(hoverUp) 
        draw.line((6, 21, 16, 11), width=2, fill=LINECOL)
        draw.line((16, 11, 26, 21), width=2, fill=LINECOL)
        draw.line((16, 11, 16, 11), width=1, fill=LINECOL)
        hoverUp = ImageTk.PhotoImage(draw._image)
        renameb = Image.new('RGBA', (SPACE, SPACE), (0,0,0,0))
        draw = ImageDraw.Draw(renameb) 
        draw.rectangle((7, 10, 25, 22), width=1, fill=None, outline=LINECOL)
        draw.line((7, 16, 16, 16), width=3, fill=LINECOL)
        draw.line((16, 8, 16, 24), width=2, fill=LINECOL)
        renameb = ImageTk.PhotoImage(draw._image)
        hoverRename = Image.new('RGBA', (SPACE, SPACE), (0,0,0,0))
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
        app.bind("<FocusIn>", drawWrapper)

        dir = Path(f'{path.dirname(image)}/')
        files: list = os_sorted([p for p in dir.glob("*") if p.suffix in FILETYPE])
        curInd: cint = files.index(image)
        
        imageLoader(files[curInd])
        
        app.mainloop()
