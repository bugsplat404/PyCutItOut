import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
from moviepy.editor import VideoFileClip, CompositeAudioClip, ImageClip, CompositeVideoClip
from moviepy.video.fx.all import crop, resize, speedx, blackwhite, rotate, lum_contrast
from moviepy.audio.fx.all import volumex
from moviepy.audio.io.AudioFileClip import AudioFileClip
import threading
import os
import cv2
import numpy as np

class VideoCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Py - Cut It Out")
        self.setup_ui()

        self.input_file = None
        self.audio_file = None
        self.watermark_text = None

    def setup_ui(self):
        notebook = ttk.Notebook(self.root, bootstyle="primary")
        notebook.pack(fill='both', expand=True)

        self.video_cut_tab = ttk.Frame(notebook)
        self.audio_extract_tab = ttk.Frame(notebook)

        notebook.add(self.video_cut_tab, text='Video Cutter')
        notebook.add(self.audio_extract_tab, text='Audio Extractor')

        self.setup_video_cutter_ui(self.video_cut_tab)
        self.setup_audio_extractor_ui(self.audio_extract_tab)

    def setup_video_cutter_ui(self, tab):
        ttk.Label(tab, text="Input Video File:").grid(row=0, column=0, padx=10, pady=10)
        self.input_file_entry = ttk.Entry(tab, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(tab, text="Browse", command=self.select_file, bootstyle="primary").grid(row=0, column=2, padx=10, pady=10)

        ttk.Label(tab, text="Input Audio File (optional):").grid(row=1, column=0, padx=10, pady=10)
        self.audio_file_entry = ttk.Entry(tab, width=50)
        self.audio_file_entry.grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(tab, text="Browse", command=self.select_audio_file, bootstyle="primary").grid(row=1, column=2, padx=10, pady=10)

        ttk.Label(tab, text="Start Time (seconds):").grid(row=2, column=0, padx=10, pady=10)
        self.start_time_var = tk.IntVar(value=0)
        self.start_time_entry = ttk.Entry(tab, textvariable=self.start_time_var)
        self.start_time_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(tab, text="End Time (seconds):").grid(row=3, column=0, padx=10, pady=10)
        self.end_time_var = tk.IntVar(value=60)
        self.end_time_entry = ttk.Entry(tab, textvariable=self.end_time_var)
        self.end_time_entry.grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(tab, text="Width:").grid(row=4, column=0, padx=10, pady=10)
        self.width_var = tk.IntVar(value=1080)
        self.width_entry = ttk.Entry(tab, textvariable=self.width_var)
        self.width_entry.grid(row=4, column=1, padx=10, pady=10)

        ttk.Label(tab, text="Height:").grid(row=5, column=0, padx=10, pady=10)
        self.height_var = tk.IntVar(value=1920)
        self.height_entry = ttk.Entry(tab, textvariable=self.height_var)
        self.height_entry.grid(row=5, column=1, padx=10, pady=10)

        # Add predefined resolutions combobox
        ttk.Label(tab, text="Select Resolution:").grid(row=6, column=0, padx=10, pady=10)
        self.resolutions = ["1080 x 1920", "720 x 1280", "480 x 640", "1920 x 1080", "1280 x 720", "640 x 480"]
        self.resolution_var = tk.StringVar()
        self.resolution_combobox = ttk.Combobox(tab, textvariable=self.resolution_var, values=self.resolutions)
        self.resolution_combobox.grid(row=6, column=1, padx=10, pady=10)
        self.resolution_combobox.bind("<<ComboboxSelected>>", self.update_resolution)

        self.video_volume_label = ttk.Label(tab, text="Video Volume: 1.0")
        self.video_volume_label.grid(row=7, column=0, padx=10, pady=10)
        self.video_volume_var = tk.DoubleVar(value=1.0)
        self.video_volume_slider = ttk.Scale(tab, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.video_volume_var, command=self.update_video_volume_label)
        self.video_volume_slider.grid(row=7, column=1, padx=10, pady=10)

        self.audio_volume_label = ttk.Label(tab, text="Audio Volume: 1.0")
        self.audio_volume_label.grid(row=8, column=0, padx=10, pady=10)
        self.audio_volume_var = tk.DoubleVar(value=1.0)
        self.audio_volume_slider = ttk.Scale(tab, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.audio_volume_var, command=self.update_audio_volume_label)
        self.audio_volume_slider.grid(row=8, column=1, padx=10, pady=10)
        
        self.video_speed_label = ttk.Label(tab, text="Video Speed: 1.0")
        self.video_speed_label.grid(row=9, column=0, padx=10, pady=10)
        self.video_speed_var = tk.DoubleVar(value=1.0)
        self.video_speed_slider = ttk.Scale(tab, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.video_speed_var, command=self.update_video_speed_label)
        self.video_speed_slider.grid(row=9, column=1, padx=10, pady=10)
        
        self.video_rotation_label = ttk.Label(tab, text="Video Rotation: 0")
        self.video_rotation_label.grid(row=10, column=0, padx=10, pady=10)
        self.video_rotation_var = tk.IntVar(value=0)
        self.video_rotation_slider = ttk.Scale(tab, from_=0, to=360, orient=tk.HORIZONTAL, variable=self.video_rotation_var, command=self.update_video_rotation_label)
        self.video_rotation_slider.grid(row=10, column=1, padx=10, pady=10)
        
        self.contrast_label = ttk.Label(tab, text="Contrast: 0.0")
        self.contrast_label.grid(row=11, column=0, padx=10, pady=10)
        self.contrast_var = tk.DoubleVar(value=0.0)
        self.contrast_slider = ttk.Scale(tab, from_=-2, to=2, orient=tk.HORIZONTAL, variable=self.contrast_var, command=self.update_contrast_label)
        self.contrast_slider.grid(row=11, column=1, padx=10, pady=10)

        self.brightness_label = ttk.Label(tab, text="Brightness: 0.0")
        self.brightness_label.grid(row=12, column=0, padx=10, pady=10)
        self.brightness_var = tk.DoubleVar(value=0.0)
        self.brightness_slider = ttk.Scale(tab, from_=-100, to=100, orient=tk.HORIZONTAL, variable=self.brightness_var, command=self.update_brightness_label)
        self.brightness_slider.grid(row=12, column=1, padx=10, pady=10)

        self.framerate_label = ttk.Label(tab, text="Framerate: 60")
        self.framerate_label.grid(row=13, column=0, padx=10, pady=10)
        self.framerate_var = tk.IntVar(value=60)
        self.framerate_entry = ttk.Entry(tab, textvariable=self.framerate_var)
        self.framerate_entry.grid(row=13, column=1, padx=10, pady=10)

        self.bitrate_label = ttk.Label(tab, text="Bitrate: 12000k")
        self.bitrate_label.grid(row=14, column=0, padx=10, pady=10)
        self.bitrate_var = tk.StringVar(value="12000k")
        self.bitrate_entry = ttk.Entry(tab, textvariable=self.bitrate_var)
        self.bitrate_entry.grid(row=14, column=1, padx=10, pady=10)

        self.add_watermark_var = tk.BooleanVar()
        self.add_watermark_checkbox = ttk.Checkbutton(tab, text="Add Watermark", variable=self.add_watermark_var)
        self.add_watermark_checkbox.grid(row=15, column=0, padx=10, pady=10)

        self.watermark_text_var = tk.StringVar()
        self.watermark_text_entry = ttk.Entry(tab, textvariable=self.watermark_text_var)
        self.watermark_text_entry.grid(row=15, column=1, padx=10, pady=10)

        ttk.Button(tab, text="Cut It Out!", command=self.cut_video, bootstyle="success").grid(row=16, column=0, columnspan=3, pady=20)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(tab, orient=tk.HORIZONTAL, length=400, mode='indeterminate', variable=self.progress_var)
        self.progress_bar.grid(row=17, column=0, columnspan=3, padx=10, pady=10)

    def update_resolution(self, event):
        resolution = self.resolution_var.get()
        width, height = map(int, resolution.split(' x '))
        self.width_var.set(width)
        self.height_var.set(height)

    def update_video_volume_label(self, value):
        self.video_volume_label.config(text=f"Video Volume: {float(value):.1f}")
        
    def update_audio_volume_label(self, value):
        self.audio_volume_label.config(text=f"Audio Volume: {float(value):.1f}")
        
    def update_video_speed_label(self, value):
        self.video_speed_label.config(text=f"Video Speed: {float(value):.1f}")
        
    def update_video_rotation_label(self, value):
        self.video_rotation_label.config(text=f"Video Rotation: {int(float(value))}")

    def update_contrast_label(self, value):
        self.contrast_label.config(text=f"Contrast: {float(value):.1f}")

    def update_brightness_label(self, value):
        self.brightness_label.config(text=f"Brightness: {float(value):.1f}")

    def setup_audio_extractor_ui(self, tab):
        ttk.Label(tab, text="Input Video File:").grid(row=0, column=0, padx=10, pady=10)
        self.audio_input_file_entry = ttk.Entry(tab, width=50)
        self.audio_input_file_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(tab, text="Browse", command=self.select_audio_input_file, bootstyle="primary").grid(row=0, column=2, padx=10, pady=10)

        ttk.Label(tab, text="Output Audio Format:").grid(row=1, column=0, padx=10, pady=10)
        self.audio_format_var = tk.StringVar(value='mp3')
        self.audio_format_entry = ttk.Entry(tab, textvariable=self.audio_format_var)
        self.audio_format_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(tab, text="Extract Audio", command=self.extract_audio, bootstyle="success").grid(row=2, column=0, columnspan=3, pady=20)

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

    def select_audio_input_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        if file_path:
            self.audio_input_file_entry.delete(0, tk.END)
            self.audio_input_file_entry.insert(0, file_path)
            self.input_file = file_path

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
            video_speed = float(self.video_speed_var.get())
            video_rotation = int(self.video_rotation_var.get())
            contrast = float(self.contrast_var.get())
            brightness = float(self.brightness_var.get())
            framerate = int(self.framerate_var.get())
            bitrate = self.bitrate_var.get()
        except ValueError:
            messagebox.showerror("Error", "Invalid input values.")
            return

        if start_time >= end_time:
            messagebox.showerror("Error", "End time must be greater than start time.")
            return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        threading.Thread(target=self.process_video, args=(start_time, end_time, width, height, video_volume, audio_volume, video_speed, video_rotation, contrast, brightness, framerate, bitrate, output_dir)).start()

    def process_video(self, start_time, end_time, width, height, video_volume, audio_volume, video_speed, video_rotation, contrast, brightness, framerate, bitrate, output_dir):
        self.progress_bar.start()

        try:
            with VideoFileClip(self.input_file) as video:
                subclip = video.subclip(start_time, end_time)

                # Apply video speed
                if video_speed != 1.0:
                    subclip = speedx(subclip, factor=video_speed)

                # Apply video rotation
                if video_rotation != 0:
                    subclip = rotate(subclip, angle=video_rotation)
                
                # Apply contrast and brightness
                if contrast != 0.0 or brightness != 0.0:
                    subclip = lum_contrast(subclip, lum=brightness, contrast=contrast)
            
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
                subclip = subclip.volumex(video_volume)

                if self.audio_file:
                    with AudioFileClip(self.audio_file) as new_audio:
                        new_audio = new_audio.volumex(audio_volume)
                        composite_audio = CompositeAudioClip([subclip.audio, new_audio])
                        subclip = subclip.set_audio(composite_audio)

                if self.add_watermark_var.get():
                    subclip = self.add_text_watermark(subclip, self.watermark_text_var.get())

                output_file = os.path.join(output_dir, f"cut_video_{start_time}_{end_time}.mp4")
                subclip.write_videofile(output_file, codec="libx264", fps=framerate, bitrate=bitrate)

            self.progress_bar.stop()
            messagebox.showinfo("Success", "Video cut and audio added successfully!")
        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_var.set(100)

    def add_text_watermark(self, video_clip, text):
        def add_text_to_frame(get_frame, t):
            frame = get_frame(t)
            overlay = frame.copy()
            alpha = 0.4  # Transparency factor

            # Position for the watermark (bottom left)
            position = (20, 40)
            
            # Adding text with transparency
            cv2.putText(overlay, text, position, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            return frame

        return video_clip.fl(add_text_to_frame, apply_to=["mask"])

    def extract_audio(self):
        if not self.input_file:
            messagebox.showerror("Error", "Please select a video file.")
            return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        try:
            with VideoFileClip(self.input_file) as video:
                audio = video.audio
                audio_output_path = os.path.join(output_dir, f"extracted_audio.{self.audio_format_var.get()}")
                audio.write_audiofile(audio_output_path)

            messagebox.showinfo("Success", f"Audio extracted successfully to {audio_output_path}!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = VideoCutterApp(root)
    root.mainloop()
