# 🎓 Modern Course Tracker 2026

A sleek, modern Windows desktop application built with **Python** and **CustomTkinter** to help students, developers, and self-learners accurately track their watch-time progress across multiple local video courses.

## ✨ Key Features

* **🧠 Smart Directory Auto-Detection:** Automatically detects whether your course directory contains categorized subfolders (Nested) or direct video files (Flat) and adapts the user interface accordingly.
* **⏱️ Accurate Watch-Time Calculation:** Scans all video files (`.mp4`, `.mkv`, `.avi`, `.mov`, `.flv`) to calculate the exact duration of each folder and the overall course duration.
* **📊 Multi-Course Dashboard:** Manage multiple courses in one place with visual progress bars and percentage indicators.
* **⚡ One-Click Selection & Launch:** Click on any folder or video to auto-fill progress inputs, or click the `▶` button to launch the video directly in your default media player.
* **💾 Automatic AppData Persistence & Backup:** Automatically saves your progress locally in the Windows `AppData` directory. Includes built-in **Export** and **Import** functionality to back up or restore your progress (`JSON`).
* **🎨 Modern Fluent UI:** Features a dark-mode interface, smooth progress bar animations, a resizable sidebar, and a custom splash screen.

## 🚀 Installation (For Users)

You don't need Python installed to use the application:
1. Go to the **Releases** section on the right side of this GitHub page.
2. Download the latest installer (`mysetup.exe`).
3. Run the installer and follow the setup wizard to install the app and create a desktop shortcut.

## 🛠️ Running from Source (For Developers)

If you want to run or modify the source code:

1. **Clone the repository:**
   `git clone https://github.com/MohammedBurghul/CourseTracker.git`
   `cd CourseTracker`

2. **Create a virtual environment and install dependencies:**
   `python -m venv .venv`
   `.venv\Scripts\activate`
   `pip install -r requirements.txt`

3. **Run the application:**
   `python main.py`

4. **Build Executable (Optional):**
   `pip install pyinstaller`
   `pyinstaller --noconsole --onefile --name "CourseTracker" main.py`

## 👨‍💻 Author

**Developed by:** Eng. Mohammed Ziad Burghul
