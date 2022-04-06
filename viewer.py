from sys import argv
from tkinter import Tk, Canvas
from PIL import Image, ImageTk, ImageDraw
import os.path
from pathlib import Path
debug = False
ICONSPACE = 30

#  fits width and height to tkinter window
def dimensionFinder(w, h):
    global app
     
    height = app.winfo_height()
    width = int(w * (height/h))
    #  Size to height of window. If that makes the image too wide, size to width instead
    return (width, height) if width <= app.winfo_width() else (app.winfo_width(), int(h * (app.winfo_width()/w)))
    
# loads image path
def imageLoader(path, drawtop):
    if not path:
        return
    global image
    global canvas
    global topbar
    global cache
    global app
    global exitb
    global minib
    global hoveredExit

    if path not in cache:
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
        b = canvas.create_image(app.winfo_width()-ICONSPACE, 0, image=exitb, anchor='nw', tag='exiter')
        b2 = canvas.create_image(app.winfo_width()-ICONSPACE-ICONSPACE, 0, image=minib, anchor='nw', tag='minimizer')
        canvas.tag_bind(b, '<Button-1>', _exit)
        canvas.tag_bind(b2, '<Button-1>', _minimize)
        canvas.tag_bind(b, '<Enter>', _hoverExit)
        canvas.tag_bind(b, '<Leave>', _removeHoverExit)
        canvas.tag_bind(b2, '<Enter>', _hoverMini)
        canvas.tag_bind(b2, '<Leave>', _removeHoverMini)

# series of functions to change icons on hover
def _removeHoverMini(event):
    global canvas
    global minib
    canvas.itemconfig('minimizer', image=minib)

def _hoverMini(event):
    global canvas
    global hoveredMini
    canvas.itemconfig('minimizer', image=hoveredMini)

def _removeHoverExit(event):
    global canvas
    global exitb
    canvas.itemconfig('exiter', image=exitb)

def _hoverExit(event):
    global canvas
    global hoveredExit
    canvas.itemconfig('exiter', image=hoveredExit)

# minimizes app
def _minimize(event):
    global app
    app.iconify()

# closes app    
def _exit(event):
    global app
    app.destroy()

# move between images when mouse scolls
def _on_mousewheel(event):
    global curInd
    global files
    global SECONDTOLAST
    global drawtop
    if event.delta > 0 and curInd > 0:
        curInd -= 1
        imageLoader(files[curInd], drawtop)
    elif event.delta < 0 and curInd < SECONDTOLAST:
        curInd += 1
        imageLoader(files[curInd], drawtop)

# clear cached images if window gets resized
def _resize(event):
    global cache
    cache = dict()

# skip clicks to menu, draws menu if not present
def _click(event):
    global curInd
    global files
    global drawtop
    if drawtop and event.y <= 24:  
        return
    drawtop = not drawtop
    imageLoader(files[curInd], drawtop)

# sometimes (inconsistently) goes blank when opening from taskbar. This redraws to prevent that
def drawWrapper(event):
    global curInd
    global files
    global drawtop
    imageLoader(files[curInd], drawtop)

if len(argv) > 1 or debug:
    image = Path(r"C:\path\for\testing") if debug else Path(argv[1])
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
    topbar = ImageTk.PhotoImage(Image.new('RGBA', (app.winfo_width(), ICONSPACE), (70, 70, 70, 160)))
    exitb = ImageTk.PhotoImage(Image.new('RGBA', (ICONSPACE, ICONSPACE), (190, 50, 50, 180)))
    hoveredExit = ImageTk.PhotoImage(Image.new('RGBA', (ICONSPACE, ICONSPACE), (190, 30, 30, 180)))
    minib = Image.new('RGBA', (ICONSPACE, ICONSPACE), (120, 120, 120, 160))
    draw = ImageDraw.Draw(minib) 
    draw.line((6, 24, 22, 24), width=2, fill=(170, 170, 170, 160))
    minib = ImageTk.PhotoImage(draw._image)
    hoveredMini = Image.new('RGBA', (ICONSPACE, ICONSPACE), (110, 110, 110, 160))
    draw = ImageDraw.Draw(hoveredMini) 
    draw.line((6, 24, 22, 24), width=2, fill=(180, 180, 180, 160))
    hoveredMini = ImageTk.PhotoImage(draw._image)

    # events based on input
    app.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-1>", _click)
    app.bind("<Configure>", _resize)
    app.bind("<FocusIn>", drawWrapper)

    dir = os.path.dirname(image)+'\\'
    files = list(p for p in Path(dir).glob("*") if p.suffix in {".png", ".jpg", ".jpeg", ".webp"})

    SECONDTOLAST = len(files)-1
    files.sort()
    curInd = files.index(image)
    
    imageLoader(files[curInd], drawtop)
    
    app.mainloop()
