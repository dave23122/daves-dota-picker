import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import json
import os
import sys
import subprocess

WINRATE_FILE = "hero_data/winRateData.json"
JSON_FILE = "hero_data/heroes.json"
HERO_DATA_DIR = 'hero_data'
HERO_IMAGES_DIR = 'hero_data/hero_images'
current_position = 3

def show_yes_no_prompt(dir_exists):
    # Create the root window and hide it
    root = tk.Tk()
    root.withdraw()

    # Show the Yes/No dialog
    if dir_exists:
        result = messagebox.askyesno("Confirmation", "Update hero data before continuing?")
    else:
        result = messagebox.askyesno("Confirmation", "Hero data is missing or invalid. Hero data update is required to continue")

    root.destroy()  # Destroy the hidden root after dialog closes

    if result:
        print("Updating hero data")
        subprocess.run(['python', 'update-heroes.py'])
        subprocess.run(['python', 'update-data.py'])
    else:
        if not dir_exists:
            print("Exiting")
            sys.exit()

# Check if hero data directory exists
if os.path.isdir(HERO_DATA_DIR):
    dir_exists = True
    print("Directory exists")
else:
    dir_exists = False
    print("Hero data directory does not exist")
show_yes_no_prompt(dir_exists)

class ScrollableUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Daves Dota Picker")
        self.geometry("1550x1120")

        # Load and sort heroes
        self.heroes = self.load_heroes()
        self.heroes.sort(key=lambda h: h["name"].lower())
        self.filtered_heroes = self.heroes.copy()
        self.image_cache = {}

        # Selection tracking
        self.selected_team = []
        self.selected_enemy = []

        # Canvas + scrollbar setup
        self.main_canvas = tk.Canvas(self)
        self.v_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.v_scrollbar.set)

        self.v_scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = ttk.Frame(self.main_canvas)
        self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.content_frame.bind("<Configure>", self.on_frame_configure)

        self.hero_buttons = {}  # maps hero['name'] and team to its Button widget
        self.hero_status = {}
        for i in self.heroes:
            self.hero_status[i['name']] = "initial"

        # Build UI
        self.build_ui()

    def load_heroes(self):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["heroes"]
    
    def reset_all(self):
        self.selected_team.clear()
        self.selected_enemy.clear()
        for i in self.heroes:
            self.hero_status[i['name']] = "initial"
        self.search_var.set("")
        self.draw_all()

    def build_ui(self):
        # Main horizontal container
        main_container = ttk.Frame(self.content_frame)
        main_container.pack(fill="x", expand=True, padx=10, pady=0)

        # LEFT FRAME: all content except Suggested Pick
        left_frame = ttk.Frame(main_container, width=1300, height=1050)
        left_frame.pack_propagate(False)  # Prevent resizing to contents
        left_frame.pack(side=tk.LEFT, fill="x", expand=True)

        # Reset Button (TOP RIGHT of left_frame)
        reset_frame = ttk.Frame(left_frame)
        reset_frame.pack(anchor="ne", pady=(0, 0))

        reset_btn = ttk.Button(reset_frame, text="Reset All", command=self.reset_all)
        reset_btn.pack()

        # Selected Heroes Section
        section_label = ttk.Label(left_frame, text="Selected Heroes", font=("Arial", 14, "bold"))
        section_label.pack(anchor="nw", pady=(0, 0))

        self.selection_frame = ttk.Frame(left_frame)
        self.selection_frame.pack(fill="x", pady=(0, 0))

        self.team_select_frame = ttk.LabelFrame(self.selection_frame, text="Your Team")
        self.team_select_frame.grid(row=0, column=0, padx=5, pady=0)
        self.team_select_frame.grid_propagate(False)
        self.team_select_frame.configure(width=250, height=80)

        self.enemy_select_frame = ttk.LabelFrame(self.selection_frame, text="Enemy Team")
        self.enemy_select_frame.grid(row=0, column=1, padx=5, pady=0)
        self.enemy_select_frame.grid_propagate(False)
        self.enemy_select_frame.configure(width=300, height=80)

        # Search
        tk.Label(left_frame, text="Search Heroes:").pack(pady=(0, 0))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.update_filter)
        search_entry = tk.Entry(left_frame, textvariable=self.search_var)
        search_entry.pack(fill="x", pady=(0, 10))

        # Team and Enemy Grids
        self.team_label = ttk.Label(left_frame, text="Team", font=("Arial", 14, "bold"))
        self.team_label.pack(anchor="w", pady=(0, 5))
        self.team_frame = ttk.Frame(left_frame)
        self.team_frame.pack(fill="x", pady=(0, 0))

        self.enemy_label = ttk.Label(left_frame, text="Enemy", font=("Arial", 14, "bold"))
        self.enemy_label.pack(anchor="w", pady=(0, 5))
        self.enemy_frame = ttk.Frame(left_frame)
        self.enemy_frame.pack(fill="x", pady=(0, 0))

        # RIGHT FRAME: Suggested Pick section
        right_frame = ttk.Frame(main_container, width=170, height=1000, borderwidth=2, relief="raised")
        right_frame.pack_propagate(False)  # Prevent shrinking
        right_frame.pack(side=tk.RIGHT, fill="y", padx=(30, 0), pady=50)

        # New Frame for Buttons 1 to 5
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(pady=(0, 10))  # Add space below the buttons
        
        self.position = ttk.Label(button_frame, text="Position 3", font=("Arial", 14, "bold"))
        self.position.pack(pady=(0, 10))

        # Create Buttons 1 to 5
        for i in range(1, 6):
            btn = ttk.Button(button_frame, text=str(i), width=3, command=lambda i=i: self.handle_position_button_click(i))
            btn.pack(side=tk.LEFT, padx=2)

        style = ttk.Style()
        style.configure("Custom.TLabelframe.Label", font=("Arial", 10))

        self.suggested_frame = ttk.LabelFrame(right_frame, text="Suggested Pick", style="Custom.TLabelframe")
        self.suggested_frame.pack(fill="both", expand=True)

        # Static container (no canvas, no scrollbar)
        self.suggested_inner = ttk.Frame(self.suggested_frame, width=170, height=1050)
        self.suggested_inner.pack(fill="both", expand=True)
        self.suggested_inner.pack_propagate(False)  # Keep fixed size if needed

        self.draw_all()

    def handle_position_button_click(self, index):
        self.position.config(text=f'Position {index}')
        global current_position
        current_position = index
        self.update_suggested_picks()

    def update_suggested_picks(self):
        global current_position
        # Clear previous suggested picks
        for widget in self.suggested_inner.winfo_children():
            widget.destroy()

        # Gather heroes still available (not in team or enemy)
        picked_names = {h["name"] for h in self.selected_team + self.selected_enemy}
        remaining_heroes = [h for h in self.heroes if h["name"] not in picked_names]

        for i in remaining_heroes:
            i['totalWinRate'] = 0

        with open(WINRATE_FILE, "r") as winRateFile:
            winRateData=json.load(winRateFile)
            # Calculate win rate for team
            for z in self.selected_team:
                for i in remaining_heroes:
                    for y in winRateData[f'{i["hero_id"]}']:
                        if y['hero'] == z['hero_id']:
                            if "totalWinRate" in i:
                                i['totalWinRate'] = i['totalWinRate'] + y['winRateWith']
                            else:
                                i['totalWinRate'] = y['winRateWith']
            # Calculate win rate for enemy
            for z in self.selected_enemy:
                for i in remaining_heroes:
                    for y in winRateData[f'{i["hero_id"]}']:
                        if y['hero'] == z['hero_id']:
                            if "totalWinRate" in i:
                                i['totalWinRate'] = i['totalWinRate'] + y['winRateVs']
                            else:
                                i['totalWinRate'] = y['winRateVs']

        # Get only heroes with the selected role
        suggested_heroes = []
        for i in remaining_heroes:
            if f'POSITION_{current_position}' in i['roles']:
                suggested_heroes.append(i)

        # Sort alphabetically by name
        suggested_heroes.sort(key=lambda x: x["totalWinRate"], reverse=True)

        # Take top 20
        suggested = suggested_heroes[:20]

        for idx, hero in enumerate(suggested):
            # Create a container frame for image + name side by side
            row_frame = ttk.Frame(self.suggested_inner)
            row_frame.grid(row=idx, column=0, sticky="w", padx=5, pady=2)

            # Hero image button (keep your existing method)
            btn = self.make_hero_button(row_frame, hero, target=None)
            btn.grid(row=0, column=0, sticky="w")

            # Hero name label next to image
            if hero["totalWinRate"] > 0:
                colour = "green"
            elif hero["totalWinRate"] == 0:
                colour = "black"
            else:
                colour = "red"
            name_label = ttk.Label(row_frame, text=f'{round(hero["totalWinRate"]*100,2)}%', font=("Arial", 8), foreground=colour)
            name_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

    def update_filter(self, *args):
        term = self.search_var.get().lower()
        self.filtered_heroes = [
            #h for h in self.heroes if term in h["name"].lower()
            h for h in self.heroes if h["name"].lower().startswith(term)
        ]
        self.draw_grids()

    def draw_all(self):
        self.update_filter()
        self.draw_selected()
        self.update_suggested_picks()

    def draw_selected(self):
        for frame in (self.team_select_frame, self.enemy_select_frame):
            for widget in frame.winfo_children():
                widget.destroy()

        # === Your Team ===
        if self.selected_team:
            for idx, hero in enumerate(self.selected_team):
                btn = self.make_hero_button(self.team_select_frame, hero, from_selection="team")
                btn.grid(row=0, column=idx, padx=4, pady=6)

        # === Enemy Team ===
        if self.selected_enemy:
            for idx, hero in enumerate(self.selected_enemy):
                btn = self.make_hero_button(self.enemy_select_frame, hero, from_selection="enemy")
                btn.grid(row=0, column=idx, padx=4, pady=6)

    def draw_grids(self):
        for frame in (self.team_frame, self.enemy_frame):
            for widget in frame.winfo_children():
                widget.destroy()

        self.populate_grid(self.team_frame, target="team")
        self.populate_grid(self.enemy_frame, target="enemy")

    def populate_grid(self, parent, target):
        cols = 22
        current_letter = None

        for idx, hero in enumerate(self.filtered_heroes):
            row, col = divmod(idx, cols)
            first_letter = hero["name"][0].upper()

            # Create a container frame for label + button (vertically stacked)
            hero_container = ttk.Frame(parent)

            # Add a label (either real or invisible placeholder)
            if first_letter != current_letter:
                current_letter = first_letter
                label = ttk.Label(hero_container, text=first_letter, font=("Arial", 10, "bold"))
            else:
                label = ttk.Label(hero_container, text=" ", font=("Arial", 10))  # Invisible spacer

            label.pack()
            btn = self.make_hero_button(hero_container, hero, from_selection=None, target=target)
            btn.pack()
            self.hero_buttons[f'{hero["name"]}-{target}'] = btn  # Store for later access

            # Place the container in the grid
            hero_container.grid(row=row, column=col, padx=4, pady=2)

    def make_hero_button(self, parent, hero, from_selection=None, target=None):
        path = hero["image"]
        if path not in self.image_cache:
            try:
                img = Image.open(path).resize((45, 35))
                self.image_cache[path] = ImageTk.PhotoImage(img)
            except Exception as e:
                print(f"Error loading image {path}: {e}")
                return tk.Button(parent, text=hero["name"])

        img = self.image_cache[path]

        if from_selection == "team":
            return tk.Button(parent, image=img, command=lambda: self.remove_hero(hero, "team"))
        elif from_selection == "enemy":
            return tk.Button(parent, image=img, command=lambda: self.remove_hero(hero, "enemy"))
        elif target == "team":
            state = tk.DISABLED if self.hero_status[hero['name']] == tk.DISABLED else tk.NORMAL
            self.hero_status[hero['name']] = state
            return tk.Button(parent, image=img, command=lambda: self.select_hero(hero, "team"), state=state)
        elif target == "enemy":
            state = tk.DISABLED if self.hero_status[hero['name']] == tk.DISABLED else tk.NORMAL
            self.hero_status[hero['name']] = state
            return tk.Button(parent, image=img, command=lambda: self.select_hero(hero, "enemy"), state=state)
        else:
            return tk.Button(parent, image=img)

    def select_hero(self, hero, team_type):
        if hero in self.selected_team or hero in self.selected_enemy:
            return
        if team_type == "team" and len(self.selected_team) < 4:
            self.selected_team.append(hero)
            # Disable the corresponding button
            if f'{hero["name"]}-team' in self.hero_buttons or f'{hero["name"]}-enemy' in self.hero_buttons:
                self.hero_buttons[f'{hero["name"]}-team']["state"] = tk.DISABLED
                self.hero_buttons[f'{hero["name"]}-enemy']["state"] = tk.DISABLED
        elif team_type == "enemy" and len(self.selected_enemy) < 5:
            self.selected_enemy.append(hero)
            # Disable the corresponding button
            if f'{hero["name"]}-team' in self.hero_buttons or f'{hero["name"]}-enemy' in self.hero_buttons:
                self.hero_buttons[f'{hero["name"]}-team']["state"] = tk.DISABLED
                self.hero_buttons[f'{hero["name"]}-enemy']["state"] = tk.DISABLED

        self.hero_status[hero['name']] = tk.DISABLED

        self.draw_selected()
        self.update_suggested_picks()

    def remove_hero(self, hero, team_type):
        if team_type == "team":
            self.selected_team.remove(hero)
        elif team_type == "enemy":
            self.selected_enemy.remove(hero)

        # Re-enable the corresponding button
        if f'{hero["name"]}-team' in self.hero_buttons or f'{hero["name"]}-enemy' in self.hero_buttons:
            try:
                self.hero_buttons[f'{hero["name"]}-team']["state"] = tk.NORMAL
                self.hero_buttons[f'{hero["name"]}-enemy']["state"] = tk.NORMAL
            except Exception as e:
                print(e)
        
        self.hero_status[hero['name']] = "initial"

        self.draw_selected()
        self.update_suggested_picks()

    def on_frame_configure(self, event):
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

if __name__ == "__main__":
    app = ScrollableUI()
    app.mainloop()
