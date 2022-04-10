#  example compile code: python -m nuitka --windows-disable-console viewer.py  (pyinstaller is very slow, please use nuitka if you plan to compile it yourself)
from sys import argv
from tkinter import Tk, Canvas, Entry
from PIL import Image, ImageTk, ImageDraw, ImageFont
from os import path, stat, rename
from send2trash import send2trash
from pathlib import Path
from ctypes import windll
from cython import int, cfunc
from bisect import insort_right

# constants
DEBUG = False
SPACE = 32
LINECOL = (170, 170, 170)
ICONCOL = (100, 104, 102)
ICONHOV = (95, 92, 88)
TOPCOL = (70, 70, 70, 160)
FILETYPE = {".png", ".jpg", ".jpeg", ".webp"}
DROPDOWNWIDTH = 190
DROPDOWNHEIGHT = 110
FONT =('cambria 11')

#  fits width and height to tkinter window
@cfunc
def dimensionFinder(w: int, h: int, dimw: int, dimh: int) -> tuple[int, int]:
    height: int
    width: int
    height = dimh
    width = int(w * (height/h))
    #  Size to height of window. If that makes the image too wide, size to width instead
    return (width, height) if width <= dimw else (dimw, int(h * (dimw/w)))
    
# loads image path
def imageLoader(path) -> None:
    if not path:
        return
    global image, canvas, topbar, cache, app, drawtop, dropDown, trueWidth, trueHeight, trueSize  # variables for drawing
    global exitb, minib, trashb, dropb, upb, renameb  # images for UI
 
    try:
        image = Image.open(path)
        if path not in cache:
            w: int
            h: int
            trueWidth, trueHeight = image.size
            trueSize = round(stat(path).st_size/1000)
            trueSize = str(round(trueSize/1000, 2))+"mb" if trueSize > 999 else str(trueSize)+"kb"
            w, h = dimensionFinder(trueWidth, trueHeight, app.winfo_width(), app.winfo_height())  # get resized dimensions for fullscreen view
            
            image = image.resize((w, h), Image.ANTIALIAS)
            image = ImageTk.PhotoImage(image)
            w = int((app.winfo_width()-w)/2)
            h = int((app.winfo_height()-h)/2)
            canvas.create_rectangle(0, 0, app.winfo_width(), app.winfo_height(), fill='black')
            canvas.create_image(w, h, image=image, anchor='nw')
            cache[path] = (image, w, h, (trueWidth, trueHeight, trueSize))
        else:
            data = cache[path]
            trueWidth, trueHeight, trueSize = data[3]
            canvas.create_rectangle(0, 0, app.winfo_width(), app.winfo_height(), fill='black')
            canvas.create_image(data[1], data[2], image=data[0], anchor='nw')
        if drawtop:
            canvas.create_image(0, 0, image=topbar, anchor='nw')
            text = canvas.create_text(36, 5, text=path.name, fill="white", anchor='nw', font=FONT)
            r = canvas.create_image(canvas.bbox(text)[2], 0, image=renameb, anchor='nw', tag='renamer')
            b = canvas.create_image(app.winfo_width()-SPACE, 0, image=exitb, anchor='nw', tag='exiter')
            b2 = canvas.create_image(app.winfo_width()-SPACE-SPACE, 0, image=minib, anchor='nw', tag='minimizer')
            t = canvas.create_image(0, 0, image=trashb, anchor='nw', tag='trasher')
            canvas.tag_bind(b, '<Button-1>', _exit)
            canvas.tag_bind(b2,'<Button-1>', _minimize)
            canvas.tag_bind(t, '<Button-1>', _trashWindow)
            canvas.tag_bind(r, '<Button-1>', _renameWindow)
            canvas.tag_bind(b, '<Enter>', _hoverExit)
            canvas.tag_bind(b, '<Leave>', _removeHoverExit)
            canvas.tag_bind(b2,'<Enter>', _hoverMini)
            canvas.tag_bind(b2,'<Leave>', _removeHoverMini)
            canvas.tag_bind(t, '<Enter>', _hoverTrash)
            canvas.tag_bind(t, '<Leave>', _removeHoverTrash)
            canvas.tag_bind(r, '<Enter>', _hoverRename)
            canvas.tag_bind(r, '<Leave>', _removeHoverRename)
            if dropDown:
                d = canvas.create_image(app.winfo_width()-(SPACE*3), 0, image=upb, anchor='nw', tag='dropper')
                createDropbar()
            else:
                d = canvas.create_image(app.winfo_width()-(SPACE*3), 0, image=dropb, anchor='nw', tag='dropper')
            canvas.tag_bind(d, '<Enter>', _hoverDrop)
            canvas.tag_bind(d, '<Leave>', _removeHoverDrop)
            canvas.tag_bind(d, '<Button-1>', _toggleDrop)
    except(FileNotFoundError):
        removeAndMove()
    

# series of functions to change icons on hover
def _removeHoverRename(event) -> None:
    global canvas, renameb
    canvas.itemconfig('renamer', image=renameb)

def _hoverRename(event) -> None:
    global canvas, hoverRename
    canvas.itemconfig('renamer', image=hoverRename)

def _removeHoverDrop(event) -> None:
    global canvas,  trashb, dropDown
    switch = upb if dropDown else dropb
    canvas.itemconfig('dropper', image=switch)

def _hoverDrop(event) -> None:
    global canvas, hoverTrash, dropDown
    switch = hoverUp if dropDown else hoverDrop
    canvas.itemconfig('dropper', image=switch)

def _removeHoverTrash(event) -> None:
    global canvas, trashb
    canvas.itemconfig('trasher', image=trashb)

def _hoverTrash(event) -> None:
    global canvas, hoverTrash
    canvas.itemconfig('trasher', image=hoverTrash)

def _removeHoverMini(event) -> None:
    global canvas, minib
    canvas.itemconfig('minimizer', image=minib)

def _hoverMini(event) -> None:
    global canvas, hoveredMini
    canvas.itemconfig('minimizer', image=hoveredMini)

def _removeHoverExit(event) -> None:
    global canvas, exitb
    canvas.itemconfig('exiter', image=exitb)

def _hoverExit(event) -> None:
    global canvas, hoveredExit
    canvas.itemconfig('exiter', image=hoveredExit)

# switches if dropdown is drawn or not
def _toggleDrop(event) -> None:
    global dropDown, canvas
    dropDown = not dropDown
    _hoverDrop(event)
    if dropDown: createDropbar()
    else: canvas.delete("dropped")

def createDropbar() -> None:
    global canvas, dropbar, dropRef, dropImage, fnt, trueWidth, trueHeight, trueSize
    draw = ImageDraw.Draw(dropbar.copy())
    draw.text((10, 25), "Pixels: "+str(trueWidth)+'x'+str(trueHeight), font=fnt, fill="white")
    draw.text((10, 60), "Size: "+trueSize, font=fnt, fill="white")
    dropImage = ImageTk.PhotoImage(draw._image)
    dropRef = canvas.create_image(app.winfo_width()-DROPDOWNWIDTH, SPACE, image=dropImage, anchor='nw', tag="dropped")
    #canvas.create_text(app.winfo_width()-DROPDOWNWIDTH+10, 5, text="test", fill="white", anchor='nw', font=('cambria 10'))
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
    global curInd, files, app, isGif, entryText
    if entryText is not None:
        deleteRenameBox()
    if isGif is not None:  # cancel gif animation before drawing new image
        isGif = None
        app.after_cancel()
    elif event.delta > 0:
        curInd = len(files)-1 if curInd == 0 else curInd-1
        imageLoader(files[curInd])
    else:
        curInd = 0 if curInd == len(files)-1 else curInd+1
        imageLoader(files[curInd])

# clear cached images if window gets resized
def _resize(event) -> None:
    global cache
    cache = dict()

# delete image
def _trashWindow(event) -> None:
    global curInd, files, image
    image = None  # error if file opened by image variable and try to delete, so set to none
    send2trash(files[curInd])
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
def _click(event) -> None:
    global curInd, files, drawtop, dropDown, app
    if drawtop and (event.y <= SPACE or (dropDown and event.x > app.winfo_width()-DROPDOWNWIDTH and event.y < SPACE+DROPDOWNHEIGHT)): 
        return
    drawtop = not drawtop
    deleteRenameBox()
    imageLoader(files[curInd])

# sometimes (inconsistently) goes blank when opening from taskbar. This redraws to prevent that
def _drawWrapper(event) -> None:
    global curInd, files
    imageLoader(files[curInd])

# opens tkinter entry to accept user input
def _renameWindow(event) -> None:
    global canvas, app, entryText
    entryText = Entry(app, font=FONT)
    entryText.insert('end', savedText)
    entryText.bind('<Return>', _renameFile)
    a = canvas.create_window(canvas.bbox('renamer')[0]+SPACE+10, 4, width=200, height=24, window=entryText, anchor='nw', tag="userinput")
    
# asks os to rename file and changes position in list to new location
def _renameFile(event):
    global entryText, files, curInd
    if entryText is None: return
    newname, oldname = str(files[curInd].parent)+'/'+entryText.get().strip()+str(files[curInd].suffix), files[curInd]
    rename(files[curInd], newname) 
    newname = Path(newname)
    del files[curInd]
    if newname < oldname: insort_right(files, newname, hi=curInd)
    else: insort_right(files, newname, lo=curInd)
    #curInd = files.index(newname)  # uncomment if you want to move with image when renamed instead of moving to next image
    deleteRenameBox()
    imageLoader(files[curInd])

def deleteRenameBox():
    global canvas, entryText, savedText
    if entryText is None: return
    savedText = entryText.get()  # comment this to remove text saving in rename window
    canvas.delete('userinput')
    entryText.destroy()
    entryText = None

if __name__ == "__main__":
    if len(argv) > 1 or DEBUG:
        image = Path(r"C:\example\some.png") if DEBUG else Path(argv[1])
        if image.suffix not in FILETYPE: exit()
        windll.shcore.SetProcessDpiAwareness(1)
        # initialize main window + important data
        drawtop, dropDown = False, False  # if given menu is drawn
        dropRef, dropImage, entryText = None, None, None  # refrences to items on menu
        savedText = ''
        fnt = ImageFont.truetype("C:/Windows/Fonts/Calibri.ttf", 22)  # font for drawing on images
        trueWidth: int
        trueHeight: int
        trueSize: int
        trueWidth, trueHeight, trueSize = 0, 0, 0  # true data of current image
        isGif = None  # None if current image not gif, else id for animation loop
        cache = dict()  # cache rendered images
        app = Tk()
        canvas = Canvas(app, bg='black', highlightthickness=0)
        canvas.pack(anchor='nw', fill='both', expand=1)

        app.attributes('-fullscreen', True)
        app.state('zoomed')
        app.update()  # updates winfo width and height to the current size, this is necessary

        # make assests for menu
        topbar = ImageTk.PhotoImage(Image.new('RGBA', (app.winfo_width(), SPACE), TOPCOL))
        dropbar = Image.new('RGBA', (DROPDOWNWIDTH, DROPDOWNHEIGHT), (50, 50, 50, 160))
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
        app.bind("<MouseWheel>", _mouseScroll)
        canvas.bind("<Button-1>", _click)
        app.bind("<Configure>", _resize)
        app.bind("<FocusIn>", _drawWrapper)

        dir = path.dirname(image)+'/'
        files = sorted(list(p for p in Path(dir).glob("*") if p.suffix in FILETYPE))
        curInd = files.index(image)
        
        imageLoader(files[curInd])
        
        app.mainloop()
