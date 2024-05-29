import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from moviepy.editor import VideoFileClip, CompositeAudioClip
from moviepy.video.fx.all import crop, resize
from moviepy.audio.fx.all import volumex
from moviepy.audio.io.AudioFileClip import AudioFileClip
import threading
import time
import os


class VideoCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Py - Cut It Out")
        self.setup_ui()
        
        self.input_file = None
        self.audio_file = None
        
    def setup_ui(self):
        ttk.Label(self.root, text="Input Video File:").grid(row=0, column=0, padx=10, pady=10)
        self.input_file_entry = ttk.Entry(self.root, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(self.root, text="Browse", command=self.select_file, bootstyle="primary").grid(row=0, column=2, padx=10, pady=10)

        ttk.Label(self.root, text="Input Audio File (optional):").grid(row=1, column=0, padx=10, pady=10)
        self.audio_file_entry = ttk.Entry(self.root, width=50)
        self.audio_file_entry.grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(self.root, text="Browse", command=self.select_audio_file, bootstyle="primary").grid(row=1, column=2, padx=10, pady=10)

        ttk.Label(self.root, text="Start Time (seconds):").grid(row=2, column=0, padx=10, pady=10)
        self.start_time_var = tk.IntVar(value=0)
        self.start_time_entry = ttk.Entry(self.root, textvariable=self.start_time_var)
        self.start_time_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(self.root, text="End Time (seconds):").grid(row=3, column=0, padx=10, pady=10)
        self.end_time_var = tk.IntVar(value=60)
        self.end_time_entry = ttk.Entry(self.root, textvariable=self.end_time_var)
        self.end_time_entry.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(self.root, text="Width:").grid(row=4, column=0, padx=10, pady=10)
        self.width_var = tk.IntVar(value=1080)
        self.width_entry = ttk.Entry(self.root, textvariable=self.width_var)
        self.width_entry.grid(row=4, column=1, padx=10, pady=10)

        ttk.Label(self.root, text="Height:").grid(row=5, column=0, padx=10, pady=10)
        self.height_var = tk.IntVar(value=1920)
        self.height_entry = ttk.Entry(self.root, textvariable=self.height_var)
        self.height_entry.grid(row=5, column=1, padx=10, pady=10)

        ttk.Label(self.root, text="Video Volume: 1.0").grid(row=6, column=0, padx=10, pady=10)
        self.video_volume_var = tk.DoubleVar(value=1.0)
        self.video_volume_slider = ttk.Scale(self.root, from_=0, to=2, orient=tk.HORIZONTAL, variable=self.video_volume_var, command=self.update_video_volume_label)
        self.video_volume_slider.grid(row=6, column=1, padx=10, pady=10)

        ttk.Label(self.root, text="Audio Volume: 1.0").grid(row=7, column=0, padx=10, pady=10)
        self.audio_volume_var = tk.DoubleVar(value=1.0)
        self.audio_volume_slider = ttk.Scale(self.root, from_=0, to=2, orient=tk.HORIZONTAL, variable=self.audio_volume_var, command=self.update_audio_volume_label)
        self.audio_volume_slider.grid(row=7, column=1, padx=10, pady=10)

        ttk.Button(self.root, text="Cut It Out!", command=self.cut_video, bootstyle="success").grid(row=8, column=0, columnspan=3, pady=20)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='indeterminate', variable=self.progress_var)
        self.progress_bar.grid(row=9, column=0, columnspan=3, padx=10, pady=10)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        if file_path:
            self.input_file_entry.delete(0, tk.END)
            self.input_file_entry.insert(0, file_path)
            with VideoFileClip(file_path) as video:
                duration = int(video.duration)
                self.end_time_var.set(duration)
            self.input_file = file_path

    def select_audio_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3;*.wav")])
        if file_path:
            self.audio_file_entry.delete(0, tk.END)
            self.audio_file_entry.insert(0, file_path)
            self.audio_file = file_path

    def cut_video(self):
        if not self.input_file:
            messagebox.showerror("Error", "Please select a video file.")
            return

        try:
            start_time = int(self.start_time_entry.get())
            end_time = int(self.end_time_entry.get())
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            video_volume = float(self.video_volume_var.get())
            audio_volume = float(self.audio_volume_var.get())
        except ValueError:
            messagebox.showerror("Error", "Start time, end time, width, height, and volume must be integers or floats.")
            return

        if start_time >= end_time:
            messagebox.showerror("Error", "End time must be greater than start time.")
            return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        threading.Thread(target=self.process_video, args=(start_time, end_time, width, height, video_volume, audio_volume, output_dir)).start()

    def process_video(self, start_time, end_time, width, height, video_volume, audio_volume, output_dir):
        self.progress_bar.start()

        try:
            with VideoFileClip(self.input_file) as video:
                subclip = video.subclip(start_time, end_time)

                original_aspect_ratio = video.size[0] / video.size[1]
                new_aspect_ratio = width / height

                if original_aspect_ratio > new_aspect_ratio:
                    new_width = int(video.size[1] * new_aspect_ratio)
                    new_height = video.size[1]
                    x_center = video.size[0] // 2
                    subclip = crop(subclip, width=new_width, height=new_height, x_center=x_center)
                elif original_aspect_ratio < new_aspect_ratio:
                    new_width = video.size[0]
                    new_height = int(video.size[0] / new_aspect_ratio)
                    y_center = video.size[1] // 2
                    subclip = crop(subclip, width=new_width, height=new_height, y_center=y_center)

                subclip = resize(subclip, newsize=(width, height))
                subclip = subclip.fx(volumex, video_volume)

                if self.audio_file:
                    with AudioFileClip(self.audio_file) as new_audio:
                        new_audio = new_audio.volumex(audio_volume)
                        composite_audio = CompositeAudioClip([subclip.audio, new_audio])
                        subclip = subclip.set_audio(composite_audio)

                output_file = os.path.join(output_dir, f"cut_video_{start_time}_{end_time}.mp4")
                subclip.write_videofile(output_file, codec="libx264")

            self.progress_bar.stop()
            messagebox.showinfo("Success", "Video cut and audio added successfully!")
        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_var.set(100)

    def update_video_volume_label(self, value):
        self.video_volume_label.config(text=f"Video Volume: {float(value):.1f}")

    def update_audio_volume_label(self, value):
        self.audio_volume_label.config(text=f"Audio Volume: {float(value):.1f}")


if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = VideoCutterApp(root)
    root.mainloop()
