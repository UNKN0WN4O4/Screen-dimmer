import tkinter as tk
from tkinter import ttk
import keyboard
import pystray
from PIL import Image, ImageDraw
import threading
import ctypes
import sys
import time

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020

class ScreenDimmer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Screen Dimmer Overlay")
        
        self.root.overrideredirect(True)
        
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        
        self.root.configure(bg='black')
        
        self.root.attributes('-topmost', True)
        
        self.brightness = 80
        self.update_overlay_alpha()
        
        self.root.after(100, self.make_click_through)
        
        self.slider_window = None
        self.slider = None
        self.slider_timer = None
        
        keyboard.add_hotkey('alt+q', self.decrease_brightness)
        keyboard.add_hotkey('alt+w', self.increase_brightness)
        
        self.setup_tray()

    def make_click_through(self):
        try:
            self.root.update()
            
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            if hwnd == 0:
                hwnd = self.root.winfo_id()
                
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            new_style = style | WS_EX_TRANSPARENT | WS_EX_LAYERED
            
            if style != new_style:
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        except Exception as e:
            print(f"Error setting click-through: {e}")

    def update_overlay_alpha(self):
        alpha = 0.9 * (1 - self.brightness / 100.0)
        self.root.attributes('-alpha', alpha)
        
        self.root.after(10, self.make_click_through)

    def show_slider(self):
        if self.slider_window is None or not self.slider_window.winfo_exists():
            self.create_slider_window()
        else:
            self.slider_window.deiconify()
            self.slider_window.lift()
        
        self.reset_slider_timer()

    def create_slider_window(self):
        self.slider_window = tk.Toplevel(self.root)
        self.slider_window.title("Brightness")
        self.slider_window.overrideredirect(True)
        self.slider_window.attributes('-topmost', True)
        self.slider_window.attributes('-alpha', 0.8)
        self.slider_window.configure(bg='#333333')
        
        w = 300
        h = 60
        x = (self.slider_window.winfo_screenwidth() // 2) - (w // 2)
        y = self.slider_window.winfo_screenheight() - h - 100
        self.slider_window.geometry(f"{w}x{h}+{x}+{y}")
        
        lbl = tk.Label(self.slider_window, text="Brightness", fg="white", bg="#333333", font=("Arial", 10))
        lbl.pack(pady=(5, 0))
        
        self.slider = ttk.Scale(self.slider_window, from_=10, to=100, orient='horizontal', command=self.on_slider_change)
        self.slider.set(self.brightness)
        self.slider.pack(fill='x', padx=20, pady=5)
        
        self.slider_window.bind('<Enter>', lambda e: self.cancel_slider_timer())
        self.slider_window.bind('<Leave>', lambda e: self.reset_slider_timer())

    def on_slider_change(self, val):
        self.brightness = float(val)
        self.update_overlay_alpha()
        self.reset_slider_timer()

    def decrease_brightness(self):
        self.brightness = max(10, self.brightness - 5)
        if self.slider:
            self.slider.set(self.brightness)
        self.update_overlay_alpha()
        self.root.after(0, self.show_slider)

    def increase_brightness(self):
        self.brightness = min(100, self.brightness + 5)
        if self.slider:
            self.slider.set(self.brightness)
        self.update_overlay_alpha()
        self.root.after(0, self.show_slider)

    def reset_slider_timer(self):
        self.cancel_slider_timer()
        self.slider_timer = self.root.after(2000, self.hide_slider)

    def cancel_slider_timer(self):
        if self.slider_timer:
            self.root.after_cancel(self.slider_timer)
            self.slider_timer = None

    def hide_slider(self):
        if self.slider_window:
            self.slider_window.withdraw()

    def create_tray_icon(self):
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color=(0, 0, 0))
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        
        def on_quit(icon, item):
            icon.stop()
            self.root.quit()
            sys.exit()

        def on_show(icon, item):
            self.root.after(0, self.show_slider)

        menu = pystray.Menu(
            pystray.MenuItem('Show Slider', on_show, default=True),
            pystray.MenuItem('Exit', on_quit)
        )

        self.icon = pystray.Icon("Dimmer", image, "Screen Dimmer", menu)
        self.icon.run()

    def setup_tray(self):
        tray_thread = threading.Thread(target=self.create_tray_icon)
        tray_thread.daemon = True
        tray_thread.start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ScreenDimmer()
    app.run()
