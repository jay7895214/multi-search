import tkinter as tk
from tkinter import simpledialog, messagebox, Scrollbar, Listbox, Canvas, Frame
import webbrowser
import os
import sys
import pickle
import subprocess
from engines_data import engines  # Import the engines list

class SearchApp:
    HISTORY_FILE = 'search_history.pkl'
    MAX_HISTORY = 50

    def __init__(self, root):
        self.root = root

        # Setting initial window dimensions based on screen width
        screen_width = root.winfo_screenwidth()
        initial_width = int(screen_width * 0.6)
        initial_height = 600
        x = (screen_width - initial_width) // 2
        y = 50
        root.geometry(f"{initial_width}x{initial_height}+{x}+{y}")

        # Create the top frame for entry, label, and certain buttons
        top_frame = Frame(root)
        top_frame.pack(fill=tk.X, side=tk.TOP, padx=20, pady=10)

        self.label = tk.Label(top_frame, text="Please enter the keyword you want to search:")
        self.label.pack(side=tk.LEFT, padx=5)

        self.entry = tk.Entry(top_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry.bind('<Return>', self.on_enter_press)

        self.search_btn = tk.Button(top_frame, text="Search", command=self.search)
        self.search_btn.pack(side=tk.RIGHT, padx=5)

        self.clear_all_btn = tk.Button(top_frame, text="Clear", command=self.clear_all)
        self.clear_all_btn.pack(side=tk.RIGHT, padx=5)

        button_frame = Frame(root)
        button_frame.pack(fill=tk.X, side=tk.TOP, padx=20)

        self.restart_btn = tk.Button(button_frame, text="Restart", command=self.restart_app)
        self.restart_btn.pack(side=tk.LEFT, padx=5)

        self.clear_engines_btn = tk.Button(button_frame, text="Clear Engines Selection", command=self.clear_engines_selection)
        self.clear_engines_btn.pack(side=tk.LEFT, padx=5)

        main_frame = Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=1, padx=20, pady=10)

        self.canvas = Canvas(main_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        scrollbar = Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self.inner_frame = Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")

        self.selected_engines = []
        self.checkbuttons = []
        self.group_checkbuttons = []

        if os.path.exists(self.HISTORY_FILE):
            with open(self.HISTORY_FILE, 'rb') as file:
                self.search_history = pickle.load(file)
        else:
            self.search_history = []

        current_column = 1
        for group, engs in sorted(engines.items(), key=lambda x: x[0]):
            frame = tk.LabelFrame(self.inner_frame, text=group)
            frame.grid(row=1, column=current_column, padx=20, pady=10, sticky="nsew", rowspan=2)

            group_var = tk.BooleanVar(value=False)
            group_check = tk.Checkbutton(frame, text="Select All", variable=group_var,
                                         command=lambda engines=sorted(engs.keys()), v=group_var: self.toggle_group(engines, v))
            group_check.grid(row=0, column=0, sticky="w", columnspan=2)
            self.group_checkbuttons.append(group_check)

            row_index = 1
            col_index = 0
            for idx, (engine, url) in enumerate(sorted(engs.items())):
                var = tk.BooleanVar()
                check = tk.Checkbutton(frame, text=engine, variable=var, 
                           command=lambda eng=engine, v=var: self.update_selected_engines(eng, v))
                check.var = var
                check.grid(row=row_index, column=col_index, sticky="w")
                self.checkbuttons.append(check)
                
                # Adjust column and row indexes when count exceeds 20
                if (idx + 1) % 20 == 0:
                    col_index += 1
                    row_index = 0  # Reset the row index

                row_index += 1

            current_column += 2 + col_index  # Adjusting the main column count based on internal columns


        history_frame = tk.LabelFrame(self.inner_frame, text="History")
        history_frame.grid(row=1, column=current_column+1, padx=20, pady=10, sticky="nsew", rowspan=3)

        history_scrollbar = Scrollbar(history_frame)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.history_listbox = Listbox(history_frame, yscrollcommand=history_scrollbar.set, width=30, height=10)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        history_scrollbar.config(command=self.history_listbox.yview)

        for item in self.search_history:
            self.history_listbox.insert(tk.END, item)

        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)

    def update_selected_engines(self, engine, var):
        if var.get():
            if engine not in self.selected_engines:
                self.selected_engines.append(engine)
        else:
            if engine in self.selected_engines:
                self.selected_engines.remove(engine)

    def toggle_group(self, group_engines, group_var):
        state = group_var.get()
        for engine in group_engines:
            if state and engine not in self.selected_engines:
                self.selected_engines.append(engine)
            elif not state and engine in self.selected_engines:
                self.selected_engines.remove(engine)

    def search(self):
        keyword = self.entry.get()
        if not keyword:
            messagebox.showerror("Error", "Please enter a keyword.")
            return

        if not self.selected_engines:
            messagebox.showerror("Error", "Please select at least one search engine.")
            return

        for engine, url in [(e, u) for group, engs in engines.items() for e, u in engs.items()]:
            if engine in self.selected_engines:
                webbrowser.open(url.format(keyword), new=1)

        self.update_history(keyword)

    def update_history(self, keyword):
        if keyword in self.search_history:
            self.search_history.remove(keyword)
        self.search_history.insert(0, keyword)
        self.search_history = self.search_history[:self.MAX_HISTORY]

        with open(self.HISTORY_FILE, 'wb') as file:
            pickle.dump(self.search_history, file)

        self.history_listbox.delete(0, tk.END)
        for item in self.search_history:
            self.history_listbox.insert(tk.END, item)

    def on_enter_press(self, event=None):
        self.search()

    def on_history_select(self, event):
        widget = event.widget
        if widget.curselection():
            index = widget.curselection()[0]
            value = widget.get(index)
            self.entry.delete(0, tk.END)
            self.entry.insert(tk.END, value)

    def clear_all(self):
        self.entry.delete(0, tk.END)

    def clear_engines_selection(self):
        for check in self.checkbuttons:
            check.deselect()
        for check in self.group_checkbuttons:
            check.deselect()
        self.selected_engines.clear()

    def restart_app(self):
        python = sys.executable
        subprocess.Popen([python] + sys.argv)
        self.root.quit()

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta//120), "units")

if __name__ == "__main__":
    root = tk.Tk()
    app = SearchApp(root)
    root.mainloop()
