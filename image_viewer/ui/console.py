from tkinter import Event, Frame, Listbox, Scrollbar


class ConsoleText(Listbox):
    def __init__(self, master) -> None:
        super().__init__(
            master,
            bg="black",
            fg="white",
            highlightcolor="black",
            highlightthickness=0,
            selectbackground="black",
            activestyle="none",
            font="arial -18",
        )

    def insert_and_scroll(self, text: str) -> None:
        """Adds text to bottom of list and move view down"""
        self.insert("end", text)
        self.yview_moveto(1)

    def insert_and_scroll_same_line(self, text: str) -> None:
        """Adds text to bottom of list and move view down"""
        self.delete("end")
        self.insert_and_scroll(text)


class Console(Frame):
    DEFAULT_PROMPT: str = ">> "

    def __init__(self, master) -> None:
        super().__init__(master, bg="black")
        listbox = ConsoleText(self)
        scrollbar = Scrollbar(self, bg="black")
        scrollbar.pack(side="right", fill="y")

        listbox.pack(expand=True, fill="both")
        self.pack(expand=True, fill="both")

        self.terminal_text: str = self.DEFAULT_PROMPT

        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        listbox.insert("end", self.terminal_text)

        listbox.bind("<Return>", self.handle_return)
        listbox.bind("<BackSpace>", self.handle_backspace)
        listbox.bind("<KeyPress>", lambda e: self.handle_keypress(e.char))
        self.listbox = listbox

    def handle_keypress(self, text: str) -> None:
        self.terminal_text = self.terminal_text + text
        self.listbox.insert_and_scroll_same_line(self.terminal_text)

    def handle_return(self, _: Event) -> None:
        if self.terminal_text == self.DEFAULT_PROMPT:
            return

        output = "test"
        self.listbox.insert(self.listbox.size(), output)

        self.terminal_text = self.DEFAULT_PROMPT

        self.listbox.insert_and_scroll(self.terminal_text)

    def handle_backspace(self, _: Event) -> None:
        if len(self.terminal_text) > 3:
            self.terminal_text = self.terminal_text[:-1]
        self.listbox.insert_and_scroll_same_line(self.terminal_text)


# if __name__ == "__main__":
#     from tkinter import Tk
#     root = Tk()
#     root.geometry("677x343")

#     terminal = Console(root)

#     root.mainloop()
