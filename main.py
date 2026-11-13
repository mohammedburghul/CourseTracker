import os
import json
import shutil 
import customtkinter as ctk
from tkinter import filedialog, messagebox

try:
    from tinytag import TinyTag
except ImportError:
    print("Missing library")
    TinyTag = None

# --- إعدادات البرنامج وحفظ البيانات ---
APP_NAME = "CourseTracker2026"
APPDATA_DIR = os.path.join(os.getenv('APPDATA'), APP_NAME)
os.makedirs(APPDATA_DIR, exist_ok=True)
SAVE_FILE = os.path.join(APPDATA_DIR, "data.json")

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

MODERN_FONT = ("Segoe UI Semibold", 13)
MODERN_FONT_BOLD = ("Segoe UI Bold", 15)
PROGRESS_FONT = ("Segoe UI Bold", 32)
ACCENT_BLUE = "#5da9ff" # اللون الأزرق المعتمد في البرنامج

def format_seconds(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:d}h {m:02d}m {s:02d}s"
    return f"{m:d}m {s:02d}s"

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes('-topmost', True)
        
        label = ctk.CTkLabel(self.tooltip_window, text=self.text, fg_color=("#2b2b2b", "#1a1a1a"), 
                             corner_radius=6, padx=12, pady=6, font=("Segoe UI", 12))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


class CourseTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("Modern Course Tracker 2026")
        
        self.geometry("1100x700+50+50")
        self.minsize(900, 600)

        self.saved_data = {"courses": {}} 
        self.current_course_id = ""
        self.course_structure = []
        self.total_course_seconds = 0
        self.active_folder_index = -1
        self.target_progress = 0.0
        self.current_animated_progress = 0.0
        self.animation_running = False
        self.is_flat_course = False 

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.intro_container = ctk.CTkFrame(self, fg_color="transparent")
        self.dashboard_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tracker_container = ctk.CTkFrame(self, fg_color="transparent")
        
        self.build_intro_ui()
        self.build_dashboard_ui()
        self.build_tracker_ui()

        self.load_data()
        self.show_splash_screen()

    # ================= 0. واجهة المقدمة =================
    def build_intro_ui(self):
        self.intro_container.grid_columnconfigure(0, weight=1)
        self.intro_container.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self.intro_container, corner_radius=15, fg_color=("gray90", "gray12"))
        card.grid(row=0, column=0, padx=50, pady=50, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(card, text="Welcome to Modern Course Tracker", font=("Segoe UI Bold", 36), text_color=("#1f538d", ACCENT_BLUE)).grid(row=0, column=0, pady=(60, 20))
        
        desc_text = (
            "This professional tool is designed to help you easily manage and track your progress across multiple local educational courses.\n\n"
            "Key Features:\n"
            "• Smart Auto-Detection: Add a folder with subfolders, or a folder directly containing videos.\n"
            "• Auto-Save & Backup: Pick up exactly where you left off. Secure your progress with Export/Import.\n"
            "• One-Click Play: Click on any video name to launch it instantly in your media player.\n\n"
            "Stay organized and finish your courses effectively!"
        )
        ctk.CTkLabel(card, text=desc_text, font=("Segoe UI", 16), justify="left", wraplength=700).grid(row=1, column=0, padx=40, pady=20)
        ctk.CTkButton(card, text="Continue ►", font=MODERN_FONT_BOLD, width=150, height=45, command=self.show_dashboard).grid(row=3, column=0, pady=(20, 60))

    # ================= 1. واجهة لوحة التحكم =================
    def build_dashboard_ui(self):
        self.dashboard_container.grid_columnconfigure(0, weight=1)
        self.dashboard_container.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.dashboard_container, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(40, 20))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="My Courses Dashboard", font=("Segoe UI Bold", 28)).grid(row=0, column=0, sticky="w")
        
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.grid(row=0, column=1, sticky="e")

        import_btn = ctk.CTkButton(actions_frame, text="⬇ Import", width=80, font=MODERN_FONT, fg_color="#2c3e50", hover_color="#34495e", command=self.import_backup)
        import_btn.pack(side="left", padx=5)
        ToolTip(import_btn, "Restore your saved progress from a backup file (.json)")

        export_btn = ctk.CTkButton(actions_frame, text="⬆ Export", width=80, font=MODERN_FONT, fg_color="#2c3e50", hover_color="#34495e", command=self.export_backup)
        export_btn.pack(side="left", padx=5)
        ToolTip(export_btn, "Save a copy of your current progress to a secure location")

        ctk.CTkButton(actions_frame, text="+ Add New Course", font=MODERN_FONT_BOLD, height=35, command=self.add_new_course).pack(side="left", padx=(15, 0))

        self.courses_list_frame = ctk.CTkScrollableFrame(self.dashboard_container, fg_color="transparent")
        self.courses_list_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=(0, 30))

        ctk.CTkLabel(self.dashboard_container, text="Developed by: Eng. Mohammed Ziad Burghul", font=("Segoe UI", 11, "italic"), text_color="gray50").grid(row=2, column=0, pady=10)

    def export_backup(self):
        if not os.path.exists(SAVE_FILE):
            messagebox.showinfo("Export", "No progress data to export yet.")
            return
        dest = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], title="Save Backup As", initialfile="CourseTracker_Backup.json")
        if dest:
            try:
                shutil.copy2(SAVE_FILE, dest)
                messagebox.showinfo("Success", "Backup exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {e}")

    def import_backup(self):
        src = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], title="Select Backup File")
        if src:
            confirm = messagebox.askyesno("Warning", "Importing a backup will overwrite your current progress. Are you sure you want to continue?")
            if confirm:
                try:
                    shutil.copy2(src, SAVE_FILE)
                    self.load_data()
                    self.refresh_dashboard()
                    messagebox.showinfo("Success", "Backup imported successfully!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to import: {e}")

    def refresh_dashboard(self):
        for widget in self.courses_list_frame.winfo_children():
            widget.destroy()

        if not self.saved_data["courses"]:
            ctk.CTkLabel(self.courses_list_frame, text="No courses added yet. Click 'Add New Course' to start.", font=MODERN_FONT, text_color="gray").pack(pady=50)
            return

        for path, data in self.saved_data["courses"].items():
            card = ctk.CTkFrame(self.courses_list_frame, corner_radius=10)
            card.pack(fill="x", pady=10, padx=10)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)
            
            ctk.CTkLabel(info_frame, text=data["name"], font=("Segoe UI Bold", 18), anchor="w").pack(fill="x")
            
            pct = data.get("progress_pct", 0.0)
            prog_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            prog_frame.pack(fill="x", pady=(10, 0))
            
            pb = ctk.CTkProgressBar(prog_frame, height=10)
            pb.pack(side="left", fill="x", expand=True, padx=(0, 15))
            pb.set(pct / 100)
            
            ctk.CTkLabel(prog_frame, text=f"{pct:.1f}%", font=MODERN_FONT_BOLD).pack(side="right")

            buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
            buttons_frame.pack(side="right", padx=20)

            ctk.CTkButton(
                buttons_frame, text="Delete", font=MODERN_FONT_BOLD, width=80, height=40,
                fg_color="#c0392b", hover_color="#e74c3c", command=lambda p=path: self.delete_course(p)
            ).pack(side="right", padx=(10, 0))

            ctk.CTkButton(
                buttons_frame, text="Resume ►", font=MODERN_FONT_BOLD, width=120, height=40, 
                command=lambda p=path: self.open_course(p)
            ).pack(side="right")

    def delete_course(self, path):
        if path in self.saved_data["courses"]:
            confirm = messagebox.askyesno("Delete Course", "Are you sure you want to delete this course?\nThis will remove all your saved progress.")
            if confirm:
                del self.saved_data["courses"][path]
                self.save_data()
                self.refresh_dashboard()

    # ================= 2. واجهة التتبع =================
    def build_tracker_ui(self):
        self.tracker_container.grid_columnconfigure(0, weight=0)
        self.tracker_container.grid_columnconfigure(1, weight=0)
        self.tracker_container.grid_columnconfigure(2, weight=1)
        self.tracker_container.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar_width = 380 
        self.sidebar_frame = ctk.CTkFrame(self.tracker_container, width=self.sidebar_width, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False) 
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_columnconfigure(1, weight=0)
        self.sidebar_frame.grid_rowconfigure(2, weight=1) 

        top_btns_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        top_btns_frame.grid(row=0, column=0, columnspan=2, padx=15, pady=(20, 10), sticky="ew")
        
        self.back_btn = ctk.CTkButton(top_btns_frame, text="◄ Dashboard", fg_color="transparent", border_width=1, font=MODERN_FONT_BOLD, command=self.show_dashboard)
        self.back_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.course_title_label = ctk.CTkLabel(self.sidebar_frame, text="", font=("Segoe UI Bold", 18), wraplength=350)
        self.course_title_label.grid(row=1, column=0, columnspan=2, padx=15, pady=(10, 20), sticky="ew")

        self.folder_scrollable_frame = ctk.CTkScrollableFrame(self.sidebar_frame, label_text="Folders (sorted)", label_font=MODERN_FONT)
        self.folder_scrollable_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        self.folder_buttons = [] # ستقوم بتخزين الحاويات (Frames) لتلوينها عند التحديد

        # Sash
        self.sash_frame = ctk.CTkFrame(self.tracker_container, width=4, fg_color="transparent", corner_radius=0)
        self.sash_frame.grid(row=0, column=1, sticky="ns")
        self.sash_frame.bind("<Enter>", lambda e: self.tracker_container.config(cursor="sb_h_double_arrow"))
        self.sash_frame.bind("<Leave>", lambda e: self.tracker_container.config(cursor="") if not getattr(self, 'resizing', False) else None)
        self.sash_frame.bind("<ButtonPress-1>", self.start_resize)
        self.sash_frame.bind("<B1-Motion>", self.do_resize)
        self.sash_frame.bind("<ButtonRelease-1>", self.stop_resize)
        self.resizing = False

        # Main Area
        self.main_frame = ctk.CTkFrame(self.tracker_container, corner_radius=15)
        self.main_frame.grid(row=0, column=2, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.progress_section = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.progress_section.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="ew")
        
        self.progress_percentage_label = ctk.CTkLabel(self.progress_section, text="0.00%", font=PROGRESS_FONT)
        self.progress_percentage_label.pack(pady=(0, 10))

        self.progressbar = ctk.CTkProgressBar(self.progress_section, width=500, height=14)
        self.progressbar.pack(pady=(0, 15))

        self.overall_duration_label = ctk.CTkLabel(self.progress_section, text="Total Duration: 00:00:00", font=MODERN_FONT)
        self.overall_duration_label.pack()

        # Input Section
        self.input_section = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color=("gray90", "gray15"))
        self.input_section.grid(row=1, column=0, padx=30, pady=10)

        self.fld_label = ctk.CTkLabel(self.input_section, text="Fld#", font=MODERN_FONT)
        self.fld_label.grid(row=0, column=0, padx=20, pady=(15, 5))
        self.folder_entry = ctk.CTkEntry(self.input_section, width=70, font=MODERN_FONT, justify="center")
        self.folder_entry.grid(row=1, column=0, padx=20, pady=(0, 15))
        
        ctk.CTkLabel(self.input_section, text="Vid#", font=MODERN_FONT).grid(row=0, column=1, padx=20, pady=(15, 5))
        self.video_entry = ctk.CTkEntry(self.input_section, width=70, font=MODERN_FONT, justify="center")
        self.video_entry.grid(row=1, column=1, padx=20, pady=(0, 15))

        ctk.CTkLabel(self.input_section, text="Time (Minutes)", font=MODERN_FONT).grid(row=0, column=2, padx=20, pady=(15, 5))
        self.time_entry = ctk.CTkEntry(self.input_section, width=100, font=MODERN_FONT, justify="center")
        self.time_entry.grid(row=1, column=2, padx=20, pady=(0, 15))

        self.update_btn = ctk.CTkButton(self.main_frame, text="Update Progress", font=MODERN_FONT_BOLD, height=40, command=self.calculate_progress)
        self.update_btn.grid(row=2, column=0, pady=(10, 20))

        self.video_list_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="Select a folder to view videos", label_font=MODERN_FONT_BOLD)
        self.video_list_frame.grid(row=3, column=0, sticky="nsew", padx=30, pady=(0, 30))
        self.main_frame.grid_rowconfigure(3, weight=1)

    # ================= التنقل والعمليات =================
    def show_intro(self):
        self.intro_container.grid(row=0, column=0, sticky="nsew")

    def show_dashboard(self):
        self.intro_container.grid_remove()
        self.tracker_container.grid_remove()
        self.refresh_dashboard()
        self.dashboard_container.grid(row=0, column=0, sticky="nsew")

    def show_tracker(self):
        self.dashboard_container.grid_remove()
        self.tracker_container.grid(row=0, column=0, sticky="nsew")

    def add_new_course(self):
        path = filedialog.askdirectory(title="Select Course Directory")
        if path:
            if path not in self.saved_data["courses"]:
                self.saved_data["courses"][path] = {
                    "name": os.path.basename(path),
                    "progress_pct": 0.0,
                    "fld": "", "vid": "", "time": ""
                }
                self.save_data()
            self.open_course(path)

    def open_course(self, path):
        if not os.path.exists(path):
            messagebox.showerror("Error", "Directory not found.")
            return
        
        self.current_course_id = path
        data = self.saved_data["courses"][path]
        
        self.course_title_label.configure(text=data["name"])
        self.folder_entry.delete(0, 'end'); self.video_entry.delete(0, 'end'); self.time_entry.delete(0, 'end')
        self.active_folder_index = -1
        self.target_progress = 0.0
        self.progressbar.set(0)
        self.progress_percentage_label.configure(text="0.00%")

        self.load_and_scan()

        if self.is_flat_course:
            self.fld_label.grid_remove()
            self.folder_entry.grid_remove()
            self.video_list_frame.grid_remove()
        else:
            self.fld_label.grid()
            self.folder_entry.grid()
            self.video_list_frame.grid()

        if data.get("fld"): self.folder_entry.insert(0, data["fld"])
        if data.get("vid"): self.video_entry.insert(0, data["vid"])
        if data.get("time"): self.time_entry.insert(0, data["time"])

        self.show_tracker()
        
        if (self.is_flat_course and data.get("vid")) or (not self.is_flat_course and data.get("fld") and data.get("vid")):
            self.calculate_progress(is_loading=True)

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    self.saved_data = json.load(f)
            except: pass
        if "courses" not in self.saved_data: self.saved_data = {"courses": {}}

    def save_data(self):
        if self.current_course_id:
            self.saved_data["courses"][self.current_course_id].update({
                "fld": self.folder_entry.get() if not self.is_flat_course else "",
                "vid": self.video_entry.get(),
                "time": self.time_entry.get(),
                "progress_pct": self.target_progress * 100
            })
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.saved_data, f)
        except Exception as e: print("Save error:", e)

    def load_and_scan(self):
        if not TinyTag: return
        self.course_structure = []
        self.total_course_seconds = 0
        path = self.current_course_id
        try:
            video_extensions = ('.mp4', '.mkv', '.avi', '.mov', '.flv')
            root_videos = sorted([v for v in os.listdir(path) if v.lower().endswith(video_extensions) and os.path.isfile(os.path.join(path, v))])
            
            if root_videos:
                self.is_flat_course = True
                video_data = []
                folder_dur = 0
                for video in root_videos:
                    try: duration = TinyTag.get(os.path.join(path, video)).duration or 0
                    except: duration = 0
                    video_data.append({"name": video, "duration": duration})
                    self.total_course_seconds += duration
                    folder_dur += duration
                self.course_structure.append({"name": "All Videos", "videos": video_data, "folder_duration": folder_dur})
                
            else:
                self.is_flat_course = False
                folders = sorted([f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))])
                for folder in folders:
                    folder_path = os.path.join(path, folder)
                    videos = sorted([v for v in os.listdir(folder_path) if v.lower().endswith(video_extensions)])
                    video_data = []
                    folder_dur = 0 # [جديد] متغير لحساب مجموع وقت المجلد الواحد
                    for video in videos:
                        try: duration = TinyTag.get(os.path.join(folder_path, video)).duration or 0
                        except: duration = 0
                        video_data.append({"name": video, "duration": duration})
                        self.total_course_seconds += duration
                        folder_dur += duration
                    self.course_structure.append({"name": folder, "videos": video_data, "folder_duration": folder_dur})
                    
            self.overall_duration_label.configure(text=f"Total Duration: {format_seconds(self.total_course_seconds)}")
            self.build_folder_sidebar()
        except: pass

    def play_video(self, video_full_path):
        try:
            os.startfile(video_full_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not play video.\n{e}")

    def build_folder_sidebar(self):
        for widget in self.folder_scrollable_frame.winfo_children(): widget.destroy()
        self.folder_buttons = []
        
        if self.is_flat_course:
            self.folder_scrollable_frame.configure(label_text="Videos List")
            
            def select_flat_vid_action(v_idx, row_frame):
                self.video_entry.delete(0, 'end')
                self.video_entry.insert(0, str(v_idx + 1))
                self.time_entry.delete(0, 'end')
                self.time_entry.insert(0, "0")
                for f_frame in self.folder_buttons:
                    f_frame.configure(fg_color="transparent")
                row_frame.configure(fg_color=("gray75", "gray25"))

            for i, vid in enumerate(self.course_structure[0]['videos']):
                time_str = format_seconds(vid['duration'])
                full_path = os.path.join(self.current_course_id, vid['name'])
                
                c = ctk.CTkFrame(self.folder_scrollable_frame, fg_color="transparent", corner_radius=8)
                c.pack(anchor="w", pady=2, padx=2)

                play_btn = ctk.CTkButton(
                    c, text="▶", font=("Segoe UI", 12), width=30,
                    anchor="center", fg_color="transparent", text_color=ACCENT_BLUE, hover_color=("gray70", "gray30"),
                    command=lambda p=full_path: self.play_video(p)
                )
                play_btn.pack(side="left")

                # [جديد] زر الوقت باللون الأزرق
                dur_btn = ctk.CTkButton(
                    c, text=f"[{time_str}]", font=("Segoe UI Semibold", 11), width=60,
                    anchor="w", fg_color="transparent", text_color=ACCENT_BLUE, hover=False,
                    command=lambda v=i, r=c: select_flat_vid_action(v, r)
                )
                dur_btn.pack(side="left")

                # زر اسم الفيديو
                select_btn = ctk.CTkButton(
                    c, text=f"{i+1:02d} | {vid['name']}", font=("Segoe UI", 12), width=1000,
                    anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                    command=lambda v=i, r=c: select_flat_vid_action(v, r)
                )
                select_btn.pack(side="left")
                
                self.folder_buttons.append(c)
        else:
            self.folder_scrollable_frame.configure(label_text="Folders (sorted)")
            for i, data in enumerate(self.course_structure):
                c = ctk.CTkFrame(self.folder_scrollable_frame, fg_color="transparent", corner_radius=8)
                c.pack(anchor="w", pady=2, padx=2)

                folder_time_str = format_seconds(data.get('folder_duration', 0))

                # [جديد] إظهار مجموع وقت المجلد باللون الأزرق بجانب الاسم
                dur_btn = ctk.CTkButton(
                    c, text=f"[{folder_time_str}]", font=("Segoe UI Semibold", 11), width=65,
                    anchor="w", fg_color="transparent", text_color=ACCENT_BLUE, hover=False,
                    command=lambda idx=i: self.show_videos_for_folder(idx)
                )
                dur_btn.pack(side="left", padx=(5, 0))

                # زر اسم المجلد
                name_btn = ctk.CTkButton(
                    c, text=f"{i+1:02d} | {data['name']}", font=("Segoe UI", 12), width=1000,
                    anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                    command=lambda idx=i: self.show_videos_for_folder(idx)
                )
                name_btn.pack(side="left")
                
                self.folder_buttons.append(c)

    def show_videos_for_folder(self, idx):
        if self.is_flat_course: return 
        if idx == self.active_folder_index: return
        
        self.folder_entry.delete(0, 'end')
        self.folder_entry.insert(0, str(idx + 1))
        
        if self.active_folder_index != -1 and self.active_folder_index < len(self.folder_buttons):
            self.folder_buttons[self.active_folder_index].configure(fg_color="transparent")
        self.folder_buttons[idx].configure(fg_color=("gray75", "gray25"))
        self.active_folder_index = idx
        
        for widget in self.video_list_frame.winfo_children(): widget.destroy()
        self.video_list_frame.configure(label_text=f"Videos in '{self.course_structure[idx]['name']}'")
        
        self.video_buttons = []
        
        def select_vid_action(v_idx, btn):
            self.video_entry.delete(0, 'end')
            self.video_entry.insert(0, str(v_idx + 1))
            self.time_entry.delete(0, 'end')
            self.time_entry.insert(0, "0")
            for v_btn in self.video_buttons:
                v_btn.configure(fg_color="transparent")
            btn.configure(fg_color=("gray75", "gray25"))

        for j, vid in enumerate(self.course_structure[idx]['videos']):
            c = ctk.CTkFrame(self.video_list_frame, fg_color="transparent")
            c.pack(fill="x", padx=5, pady=2)
            
            full_path = os.path.join(self.current_course_id, self.course_structure[idx]['name'], vid['name'])
            
            play_btn = ctk.CTkButton(
                c, text="▶", font=MODERN_FONT, width=30,
                anchor="center", fg_color="transparent", text_color=ACCENT_BLUE, hover_color=("gray70", "gray30"),
                command=lambda p=full_path: self.play_video(p)
            )
            play_btn.pack(side="left")
            
            select_btn = ctk.CTkButton(
                c, text=f"{j+1:02d}. {vid['name']}", font=MODERN_FONT, 
                anchor="w", fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray70", "gray30")
            )
            select_btn.configure(command=lambda v=j, b=select_btn: select_vid_action(v, b))
            select_btn.pack(side="left", fill="x", expand=True)
            self.video_buttons.append(select_btn)
            
            ctk.CTkLabel(c, text=format_seconds(vid['duration']), font=MODERN_FONT, text_color=ACCENT_BLUE).pack(side="right", padx=10)

    def calculate_progress(self, is_loading=False):
        try:
            f_idx = 0 if self.is_flat_course else int(self.folder_entry.get().strip()) - 1
            v_idx = int(self.video_entry.get().strip()) - 1
            curr_sec = int(self.time_entry.get().strip() or "0") * 60
            
            if f_idx < 0 or f_idx >= len(self.course_structure): return
            if v_idx < 0 or v_idx >= len(self.course_structure[f_idx]["videos"]): return

            watched = sum(v["duration"] for i in range(f_idx) for v in self.course_structure[i]["videos"])
            watched += sum(self.course_structure[f_idx]["videos"][j]["duration"] for j in range(v_idx))
            watched += curr_sec
            
            pct = max(0.0, min((watched / self.total_course_seconds) * 100, 100.0)) if self.total_course_seconds else 0.0
            
            self.progress_percentage_label.configure(text=f"{pct:.2f}%")
            self.animate_progressbar(pct / 100)
            
            if not is_loading: self.save_data()
        except: pass

    def animate_progressbar(self, target):
        self.target_progress = target
        if not self.animation_running:
            self.animation_running = True
            self._update_animation_step()

    def _update_animation_step(self):
        step = 0.02
        if abs(self.current_animated_progress - self.target_progress) < step:
            self.current_animated_progress = self.target_progress
            self.progressbar.set(self.current_animated_progress)
            self.animation_running = False
        else:
            self.current_animated_progress += step if self.current_animated_progress < self.target_progress else -step
            self.progressbar.set(self.current_animated_progress)
            self.after(10, self._update_animation_step)

    def start_resize(self, event):
        self.resizing = True
        self.start_x = event.x_root
    def do_resize(self, event):
        if self.resizing:
            new_width = self.sidebar_width + (event.x_root - self.start_x)
            if 200 < new_width < 700:
                self.sidebar_width = new_width
                self.sidebar_frame.configure(width=self.sidebar_width)
                self.start_x = event.x_root
    def stop_resize(self, event):
        self.resizing = False
        self.tracker_container.config(cursor="")

    def show_splash_screen(self):
        splash = ctk.CTkToplevel(self)
        splash.overrideredirect(True)
        splash.attributes('-topmost', True)
        width, height = 600, 350
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        splash.geometry(f"{width}x{height}+{x}+{y}")
        splash.configure(fg_color=("gray95", "#1c1c1c"))

        ctk.CTkLabel(splash, text="Modern Course Tracker", font=("Segoe UI Bold", 36)).pack(pady=(70, 10))
        ctk.CTkLabel(splash, text="Loading your workspace...", font=("Segoe UI", 16), text_color="gray").pack(pady=(0, 30))
        progress = ctk.CTkProgressBar(splash, width=400, height=8); progress.pack(pady=10); progress.set(0)
        ctk.CTkLabel(splash, text="Developed by: Eng. Mohammed Ziad Burghul", font=("Segoe UI", 13, "italic"), text_color="#1f538d").pack(side="bottom", pady=30)

        def update_progress(val=0):
            if val <= 1.0:
                progress.set(val)
                splash.after(15, lambda: update_progress(val + 0.02))
            else:
                splash.destroy()
                self.deiconify()
                self.show_intro()

        update_progress()

if __name__ == "__main__":
    app = CourseTrackerApp()
    app.mainloop()