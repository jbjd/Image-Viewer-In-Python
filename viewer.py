#  example compile code: python -m nuitka --windows-disable-console viewer.py  (pyinstaller is very slow, please use nuitka if you plan to compile it yourself)
from sys import argv
from tkinter import Tk, Canvas
from PIL import Image, ImageTk, ImageDraw
from os import path
from send2trash import send2trash
from pathlib import Path
from ctypes import windll
from cython import int, cfunc
windll.shcore.SetProcessDpiAwareness(1)
debug = False
SPACE = 32
LINECOL = (170, 170, 170)
ICONCOL = (100, 104, 102)
ICONHOV = (95, 92, 88)

#  fits width and height to tkinter window
@cfunc
def dimensionFinder(w: int, h: int) -> tuple[int, int]:
    global app
    height: int
    width: int
    height = app.winfo_height()
    width = int(w * (height/h))
    #  Size to height of window. If that makes the image too wide, size to width instead
    return (width, height) if width <= app.winfo_width() else (app.winfo_width(), int(h * (app.winfo_width()/w)))
    
# loads image path
def imageLoader(path, drawtop) -> None:
    if not path:
        return
    global image
    global canvas
    global topbar
    global cache
    global app
    global exitb
    global minib
    global trashb

    if path not in cache:
        w: int
        h: int
        image = Image.open(path)
        w, h = image.size
        w, h = dimensionFinder(w, h)  # get resized dimensions for fullscreen view
        
        image = image.resize((w, h), Image.ANTIALIAS)
        image = ImageTk.PhotoImage(image)
        w = int((app.winfo_width()-w)/2)
        h = int((app.winfo_height()-h)/2)
        canvas.create_rectangle(0, 0, app.winfo_width(), app.winfo_height(), fill='black')
        canvas.create_image(w, h, image=image, anchor='nw')
        cache[path] = (image, w, h)
    else:
        data = cache[path]
        canvas.create_rectangle(0, 0, app.winfo_width(), app.winfo_height(), fill='black')
        canvas.create_image(data[1], data[2], image=data[0], anchor='nw')
    if drawtop:
        canvas.create_image(0, 0, image=topbar, anchor='nw')
        canvas.create_text(36, 5, text=path.name, fill="white", anchor='nw', font=('cambria 11'))
        b = canvas.create_image(app.winfo_width()-SPACE, 0, image=exitb, anchor='nw', tag='exiter')
        b2 = canvas.create_image(app.winfo_width()-SPACE-SPACE, 0, image=minib, anchor='nw', tag='minimizer')
        t = canvas.create_image(0, 0, image=trashb, anchor='nw', tag='trasher')
        canvas.tag_bind(b, '<Button-1>', _exit)
        canvas.tag_bind(b2,'<Button-1>', _minimize)
        canvas.tag_bind(t, '<Button-1>', _trashWindow)
        canvas.tag_bind(b, '<Enter>', _hoverExit)
        canvas.tag_bind(b, '<Leave>', _removeHoverExit)
        canvas.tag_bind(b2,'<Enter>', _hoverMini)
        canvas.tag_bind(b2,'<Leave>', _removeHoverMini)
        canvas.tag_bind(t, '<Enter>', _hoverTrash)
        canvas.tag_bind(t, '<Leave>', _removeHoverTrash)

# series of functions to change icons on hover
def _removeHoverTrash(event) -> None:
    global canvas
    global trashb
    canvas.itemconfig('trasher', image=trashb)

def _hoverTrash(event) -> None:
    global canvas
    global hoverTrash
    canvas.itemconfig('trasher', image=hoverTrash)

def _removeHoverMini(event) -> None:
    global canvas
    global minib
    canvas.itemconfig('minimizer', image=minib)

def _hoverMini(event) -> None:
    global canvas
    global hoveredMini
    canvas.itemconfig('minimizer', image=hoveredMini)

def _removeHoverExit(event) -> None:
    global canvas
    global exitb
    canvas.itemconfig('exiter', image=exitb)

def _hoverExit(event) -> None:
    global canvas
    global hoveredExit
    canvas.itemconfig('exiter', image=hoveredExit)

# minimizes app
def _minimize(event) -> None:
    global app
    app.iconify()

# closes app    
def _exit(event) -> None:
    global app
    app.quit()

# move between images when mouse scolls
def _mouseScroll(event) -> None:
    global curInd
    global files
    global secondToLast
    global drawtop
    if event.delta > 0 and curInd > 0:
        curInd -= 1
        imageLoader(files[curInd], drawtop)
    elif event.delta < 0 and curInd < secondToLast:
        curInd += 1
        imageLoader(files[curInd], drawtop)

# clear cached images if window gets resized
def _resize(event) -> None:
    global cache
    cache = dict()

# ask user if they want to delete image
def _trashWindow(event) -> None:
    global curInd
    global files
    global drawtop
    global secondToLast
    send2trash(files[curInd])
    del files[curInd]
    secondToLast = len(files)-1
    if curInd >= len(files):
        curInd = len(files)-1
    imageLoader(files[curInd], drawtop)

# skip clicks to menu, draws menu if not present
def _click(event) -> None:
    global curInd
    global files
    global drawtop
    if drawtop and event.y <= 24:  
        return
    drawtop = not drawtop
    imageLoader(files[curInd], drawtop)

# sometimes (inconsistently) goes blank when opening from taskbar. This redraws to prevent that
def drawWrapper(event) -> None:
    global curInd
    global files
    global drawtop
    imageLoader(files[curInd], drawtop)

if len(argv) > 1 or debug:
    image = Path(r"C:\place\thing.png") if debug else Path(argv[1])
    # initialize main window + important data
    drawtop = False  # bool if menu at top is drawn
    cache = dict()  # cache calculated data on images
    app = Tk()
    canvas = Canvas(app, bg='black', highlightthickness=0)
    canvas.pack(anchor='nw', fill='both', expand=1)

    app.attributes('-fullscreen', True)
    app.state('zoomed')
    app.update()  # updates winfo width and height to the current size, this is necessary

    # make assests for menu
    topbar = ImageTk.PhotoImage(Image.new('RGBA', (app.winfo_width(), SPACE), (70, 70, 70, 160)))
    exitb = ImageTk.PhotoImage(Image.new('RGBA', (SPACE, SPACE), (190, 40, 40)))
    hoveredExit = Image.new('RGBA', (SPACE, SPACE), (180, 25, 20))
    draw = ImageDraw.Draw(hoveredExit) 
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

    # events based on input
    app.bind("<MouseWheel>", _mouseScroll)
    canvas.bind("<Button-1>", _click)
    app.bind("<Configure>", _resize)
    app.bind("<FocusIn>", drawWrapper)

    dir = path.dirname(image)+'/'
    files = list(p for p in Path(dir).glob("*") if p.suffix in {".png", ".jpg", ".jpeg", ".webp"})

    secondToLast = len(files)-1
    files.sort()
    curInd = files.index(image)
    
    imageLoader(files[curInd], drawtop)
    
    app.mainloop()
