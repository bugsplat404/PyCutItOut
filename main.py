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
        self.video_compress_tab = ttk.Frame(notebook)

        notebook.add(self.video_cut_tab, text='Video Cutter')
        notebook.add(self.audio_extract_tab, text='Audio Extractor')
        notebook.add(self.video_compress_tab, text='Video Compressor')

        self.setup_video_cutter_ui(self.video_cut_tab)
        self.setup_audio_extractor_ui(self.audio_extract_tab)
        self.setup_video_compressor_ui(self.video_compress_tab)

    def setup_video_cutter_ui(self, tab):
        main_frame = ttk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True)

        basic_settings_frame = ttk.Labelframe(main_frame, text="Basic Settings")
        basic_settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        advanced_settings_frame = ttk.Labelframe(main_frame, text="Advanced Settings")
        advanced_settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Basic Settings
        ttk.Label(basic_settings_frame, text="Input Video File:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.input_file_entry = ttk.Entry(basic_settings_frame, width=50)
        self.input_file_entry.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        ttk.Button(basic_settings_frame, text="Browse", command=self.select_file, bootstyle="primary").grid(row=0, column=2, padx=10, pady=10)

        ttk.Label(basic_settings_frame, text="Input Audio File (optional):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.audio_file_entry = ttk.Entry(basic_settings_frame, width=50)
        self.audio_file_entry.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        ttk.Button(basic_settings_frame, text="Browse", command=self.select_audio_file, bootstyle="primary").grid(row=1, column=2, padx=10, pady=10)

        ttk.Label(basic_settings_frame, text="Start Time (seconds):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.start_time_var = tk.IntVar(value=0)
        self.start_time_entry = ttk.Entry(basic_settings_frame, textvariable=self.start_time_var)
        self.start_time_entry.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(basic_settings_frame, text="End Time (seconds):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.end_time_var = tk.IntVar(value=60)
        self.end_time_entry = ttk.Entry(basic_settings_frame, textvariable=self.end_time_var)
        self.end_time_entry.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(basic_settings_frame, text="Width:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        self.width_var = tk.IntVar(value=1080)
        self.width_entry = ttk.Entry(basic_settings_frame, textvariable=self.width_var)
        self.width_entry.grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)

        ttk.Label(basic_settings_frame, text="Height:").grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        self.height_var = tk.IntVar(value=1920)
        self.height_entry = ttk.Entry(basic_settings_frame, textvariable=self.height_var)
        self.height_entry.grid(row=5, column=1, padx=10, pady=10, sticky=tk.W)

        # Add predefined resolutions combobox
        ttk.Label(basic_settings_frame, text="Select Resolution:").grid(row=6, column=0, padx=10, pady=10, sticky=tk.W)
        self.resolutions = ["<-- Hochformat -->", "1080 x 1920", "720 x 1280", "480 x 640", "<-- Querformat -->", "1920 x 1080", "1280 x 720", "640 x 480"]
        self.resolution_var = tk.StringVar(value="1080 x 1920")
        self.resolution_combobox = ttk.Combobox(basic_settings_frame, textvariable=self.resolution_var, values=self.resolutions)
        self.resolution_combobox.grid(row=6, column=1, padx=10, pady=10, sticky=tk.W)
        self.resolution_combobox.bind("<<ComboboxSelected>>", self.update_resolution)

        ttk.Button(basic_settings_frame, text="Cut It Out!", command=self.cut_video, bootstyle="success").grid(row=7, column=0, columnspan=3, pady=20)

        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(basic_settings_frame, orient=tk.HORIZONTAL, length=400, mode='indeterminate', variable=self.progress_var)
        self.progress_bar.grid(row=8, column=0, columnspan=3, padx=10, pady=10)

        # Advanced Settings
        self.show_advanced = tk.BooleanVar(value=False)
        self.show_advanced_checkbutton = ttk.Checkbutton(main_frame, text="Show More Settings", variable=self.show_advanced, command=self.toggle_advanced_settings)
        self.show_advanced_checkbutton.pack(padx=10, pady=10)

        self.advanced_widgets = []

        self.video_volume_label = ttk.Label(advanced_settings_frame, text="Video Volume: 1.0")
        self.video_volume_label.grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.video_volume_var = tk.DoubleVar(value=1.0)
        self.video_volume_slider = ttk.Scale(advanced_settings_frame, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.video_volume_var, command=self.update_video_volume_label)
        self.video_volume_slider.grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.video_volume_label, self.video_volume_slider])

        self.audio_volume_label = ttk.Label(advanced_settings_frame, text="Audio Volume: 1.0")
        self.audio_volume_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.audio_volume_var = tk.DoubleVar(value=1.0)
        self.audio_volume_slider = ttk.Scale(advanced_settings_frame, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.audio_volume_var, command=self.update_audio_volume_label)
        self.audio_volume_slider.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.audio_volume_label, self.audio_volume_slider])

        self.video_speed_label = ttk.Label(advanced_settings_frame, text="Video Speed: 1.0")
        self.video_speed_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.video_speed_var = tk.DoubleVar(value=1.0)
        self.video_speed_slider = ttk.Scale(advanced_settings_frame, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.video_speed_var, command=self.update_video_speed_label)
        self.video_speed_slider.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.video_speed_label, self.video_speed_slider])

        self.video_rotation_label = ttk.Label(advanced_settings_frame, text="Video Rotation: 0")
        self.video_rotation_label.grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.video_rotation_var = tk.IntVar(value=0)
        self.video_rotation_slider = ttk.Scale(advanced_settings_frame, from_=0, to=360, orient=tk.HORIZONTAL, variable=self.video_rotation_var, command=self.update_video_rotation_label)
        self.video_rotation_slider.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.video_rotation_label, self.video_rotation_slider])

        self.contrast_label = ttk.Label(advanced_settings_frame, text="Contrast: 0.0")
        self.contrast_label.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        self.contrast_var = tk.DoubleVar(value=0.0)
        self.contrast_slider = ttk.Scale(advanced_settings_frame, from_=-2, to=2, orient=tk.HORIZONTAL, variable=self.contrast_var, command=self.update_contrast_label)
        self.contrast_slider.grid(row=4, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.contrast_label, self.contrast_slider])

        self.brightness_label = ttk.Label(advanced_settings_frame, text="Brightness: 0.0")
        self.brightness_label.grid(row=5, column=0, padx=10, pady=10, sticky=tk.W)
        self.brightness_var = tk.DoubleVar(value=0.0)
        self.brightness_slider = ttk.Scale(advanced_settings_frame, from_=-100, to=100, orient=tk.HORIZONTAL, variable=self.brightness_var, command=self.update_brightness_label)
        self.brightness_slider.grid(row=5, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.brightness_label, self.brightness_slider])

        self.framerate_label = ttk.Label(advanced_settings_frame, text="Framerate: 60")
        self.framerate_label.grid(row=6, column=0, padx=10, pady=10, sticky=tk.W)
        self.framerate_var = tk.IntVar(value=60)
        self.framerate_entry = ttk.Entry(advanced_settings_frame, textvariable=self.framerate_var)
        self.framerate_entry.grid(row=6, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.framerate_label, self.framerate_entry])

        self.bitrate_label = ttk.Label(advanced_settings_frame, text="Bitrate")
        self.bitrate_label.grid(row=7, column=0, padx=10, pady=10, sticky=tk.W)
        self.bitrate_var = tk.StringVar(value="12000")
        self.bitrate_entry = ttk.Entry(advanced_settings_frame, textvariable=self.bitrate_var)
        self.bitrate_entry.grid(row=7, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.extend([self.bitrate_label, self.bitrate_entry])

        self.add_watermark_var = tk.BooleanVar()
        self.add_watermark_checkbox = ttk.Checkbutton(advanced_settings_frame, text="Add Watermark", variable=self.add_watermark_var)
        self.add_watermark_checkbox.grid(row=8, column=0, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.append(self.add_watermark_checkbox)

        self.watermark_text_var = tk.StringVar()
        self.watermark_text_entry = ttk.Entry(advanced_settings_frame, textvariable=self.watermark_text_var)
        self.watermark_text_entry.grid(row=8, column=1, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.append(self.watermark_text_entry)
        
        self.watermark_position_var = tk.StringVar(value="Top Left")
        self.watermark_position_combobox = ttk.Combobox(advanced_settings_frame, textvariable=self.watermark_position_var, values=["Top Left", "Top Right", "Bottom Left", "Bottom Right", "Center"])
        self.watermark_position_combobox.grid(row=8, column=2, padx=10, pady=10, sticky=tk.W)
        self.advanced_widgets.append(self.watermark_position_combobox)

        # Hide advanced settings initially
        self.toggle_advanced_settings()
        
    def toggle_advanced_settings(self):
        if self.show_advanced.get():
            for widget in self.advanced_widgets:
                widget.grid()
        else:
            for widget in self.advanced_widgets:
                widget.grid_remove()
                
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

    def setup_video_compressor_ui(self, tab):
        ttk.Label(tab, text="Input Video File:").grid(row=0, column=0, padx=10, pady=10)
        self.compress_input_file_entry = ttk.Entry(tab, width=50)
        self.compress_input_file_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(tab, text="Browse", command=self.select_compress_file, bootstyle="primary").grid(row=0, column=2, padx=10, pady=10)

        ttk.Label(tab, text="Width:").grid(row=1, column=0, padx=10, pady=10)
        self.compress_width_var = tk.IntVar(value=1080)
        self.compress_width_entry = ttk.Entry(tab, textvariable=self.compress_width_var)
        self.compress_width_entry.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(tab, text="Height:").grid(row=2, column=0, padx=10, pady=10)
        self.compress_height_var = tk.IntVar(value=1920)
        self.compress_height_entry = ttk.Entry(tab, textvariable=self.compress_height_var)
        self.compress_height_entry.grid(row=2, column=1, padx=10, pady=10)

        ttk.Label(tab, text="Output Resolution:").grid(row=3, column=0, padx=10, pady=10)
        self.compress_resolutions = ["<-- Hochformat -->", "1080 x 1920", "720 x 1280", "480 x 640", "<-- Querformat -->", "1920 x 1080", "1280 x 720", "640 x 480"]
        self.compress_resolution_var = tk.StringVar(value="1080 x 1920")
        self.compress_resolution_combobox = ttk.Combobox(tab, textvariable=self.compress_resolution_var, values=self.compress_resolutions)
        self.compress_resolution_combobox.grid(row=3, column=1, padx=10, pady=10)
        self.compress_resolution_combobox.bind("<<ComboboxSelected>>", self.update_compress_resolution)
        
        self.compress_framerate_label = ttk.Label(tab, text="Framerate: 60")
        self.compress_framerate_label.grid(row=4, column=0, padx=10, pady=10)
        self.compress_framerate_var = tk.IntVar(value=60)
        self.compress_framerate_entry = ttk.Entry(tab, textvariable=self.compress_framerate_var)
        self.compress_framerate_entry.grid(row=4, column=1, padx=10, pady=10)

        ttk.Label(tab, text="Video Bitrate (kbps):").grid(row=5, column=0, padx=10, pady=10)
        self.compress_bitrate_var = tk.StringVar(value="4000")
        self.compress_bitrate_entry = ttk.Entry(tab, textvariable=self.compress_bitrate_var)
        self.compress_bitrate_entry.grid(row=5, column=1, padx=10, pady=10)

        ttk.Label(tab, text="Audio Bitrate (kbps):").grid(row=6, column=0, padx=10, pady=10)
        self.compress_audio_bitrate_var = tk.StringVar(value="256")
        self.compress_audio_bitrate_entry = ttk.Entry(tab, textvariable=self.compress_audio_bitrate_var)
        self.compress_audio_bitrate_entry.grid(row=6, column=1, padx=10, pady=10)
        
        self.compress_video_volume_label = ttk.Label(tab, text="Video Volume: 1.0")
        self.compress_video_volume_label.grid(row=7, column=0, padx=10, pady=10)
        self.compress_video_volume_var = tk.DoubleVar(value=1.0)
        self.compress_video_volume_slider = ttk.Scale(tab, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.compress_video_volume_var, command=self.update_compress_video_volume_label)
        self.compress_video_volume_slider.grid(row=7, column=1, padx=10, pady=10)
        
        self.compress_video_tone_label = ttk.Label(tab, text="Video Tone: 1.0")
        self.compress_video_tone_label.grid(row=8, column=0, padx=10, pady=10)
        self.compress_video_tone_var = tk.DoubleVar(value=1.0)
        self.compress_video_tone_slider = ttk.Scale(tab, from_=0, to=3, orient=tk.HORIZONTAL, variable=self.compress_video_tone_var, command=self.update_compress_video_tone_label)
        self.compress_video_tone_slider.grid(row=8, column=1, padx=10, pady=10)

        ttk.Button(tab, text="Compress Video", command=self.compress_video, bootstyle="success").grid(row=11, column=0, columnspan=3, pady=20)


    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        if file_path:
            self.input_file_entry.delete(0, tk.END)
            self.input_file_entry.insert(0, file_path)
            with VideoFileClip(file_path) as video:
                duration = int(video.duration)
                fps = video.fps
                width, height = video.size
                resolution = f"{width} x {height}"
                self.width_var.set(width)
                self.height_var.set(height)
                self.resolution_var.set(resolution)
                self.end_time_var.set(duration)
                self.framerate_var.set(fps)
                self.bitrate_var.set("12000")
            self.input_file = file_path

    def select_audio_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3;*.wav")])
        if file_path:
            self.audio_file_entry.delete(0, tk.END)
            self.audio_file_entry.insert(0, file_path)
            self.audio_file = file_path
            
    def select_compress_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
        if file_path:
            self.compress_input_file_entry.delete(0, tk.END)
            self.compress_input_file_entry.insert(0, file_path)
            self.input_file = file_path
            with VideoFileClip(file_path) as video:
                fps = video.fps
                width, height = video.size
                resolution = f"{width} x {height}"
                self.compress_width_var.set(width)
                self.compress_height_var.set(height)
                self.compress_resolution_var.set(resolution)
                self.compress_framerate_var.set(fps)
                
    def update_compress_resolution(self, event):
        resolution = self.compress_resolution_var.get()
        width, height = map(int, resolution.split(' x '))
        self.compress_width_var.set(width)
        self.compress_height_var.set(height)
        
    def update_compress_video_volume_label(self, value):
        self.compress_video_volume_label.config(text=f"Video Volume: {float(value):.1f}")
        
    def update_compress_video_tone_label(self, value):
        self.compress_video_tone_label.config(text=f"Audio Tone: {float(value):.1f}")
        

    def compress_video(self):
        if not self.input_file:
            messagebox.showerror("Error", "Please select a video file.")
            return

        try:
            width = int(self.compress_width_var.get())
            height = int(self.compress_height_var.get())
            framerate = int(self.compress_framerate_var.get())
            video_bitrate = int(self.compress_bitrate_var.get())
            audio_bitrate = int(self.compress_audio_bitrate_var.get())
            volume = float(self.compress_video_volume_var.get())
            tone = float(self.compress_video_tone_var.get())
        except ValueError:
            messagebox.showerror("Error", "Bitrate must be an integer.")
            return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        threading.Thread(target=self.process_compress_video, args=(width, height, output_dir, framerate, video_bitrate, audio_bitrate, volume, tone)).start()

    def process_compress_video(self, width, height, output_dir, framerate, video_bitrate, audio_bitrate, volume=1.0, tone=1.0):
        self.progress_bar.start()

        try:
            with VideoFileClip(self.input_file) as video:
                subclip = resize(video, newsize=(width, height))
                
                # Adjust volume
                if volume <= 0:
                    raise ValueError("Volume limit must be a positive value.")
                if volume != 1.0:
                    subclip = subclip.fx(volumex, volume)

                # Set tone
                if tone <= 0:
                    raise ValueError("Volume limit must be a positive value.")
                if tone != 1.0:
                    subclip = subclip.fx(volumex, tone)
                
                output_file = os.path.join(output_dir, f"compressed_video_{framerate}_{video_bitrate}.mp4")
                
                # Encoder: libx264, h264_nvenc, hevc_nvenc
                subclip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=framerate, bitrate=f"{video_bitrate}k", audio_bitrate=f"{audio_bitrate}k", preset="slow", audio_fps=48000)

            self.progress_bar.stop()
            messagebox.showinfo("Success", "Video compressed successfully!")
        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_var.set(100)

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
            video_bitrate = self.bitrate_var.get()
        except ValueError:
            messagebox.showerror("Error", "Invalid input values.")
            return

        if start_time >= end_time:
            messagebox.showerror("Error", "End time must be greater than start time.")
            return

        output_dir = filedialog.askdirectory()
        if not output_dir:
            return

        threading.Thread(target=self.process_video, args=(start_time, end_time, width, height, video_volume, audio_volume, video_speed, video_rotation, contrast, brightness, framerate, video_bitrate, output_dir)).start()

    def process_video(self, start_time, end_time, width, height, video_volume, audio_volume, video_speed, video_rotation, contrast, brightness, framerate, video_bitrate, output_dir):
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
                    subclip = self.add_text_watermark(subclip, self.watermark_text_var.get(), self.watermark_position_var.get())

                output_file = os.path.join(output_dir, f"cut_video_{start_time}_{end_time}.mp4")
                
                subclip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=framerate, bitrate=f"{video_bitrate}k", preset="slow", audio_fps=48000)

            self.progress_bar.stop()
            messagebox.showinfo("Success", "Video cut and audio added successfully!")
        except Exception as e:
            self.progress_bar.stop()
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_var.set(100)

    def add_text_watermark(self, video_clip, text, position="Top Left"):
        def add_text_to_frame(get_frame, t):
            frame = get_frame(t)
            overlay = frame.copy()
            alpha = 0.4  # Transparency factor
            
            # Get frame dimensions
            h, w = frame.shape[:2]

            # Calculate positions
            positions = {
                "Top Left": (20, 40),
                "Top Right": (w - 20 - cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][0], 40),
                "Bottom Left": (20, h - 20),
                "Bottom Right": (w - 20 - cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][0], h - 20),
                "Center": ((w - cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][0]) // 2, (h + cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][1]) // 2)
            }
            
            pos = positions.get(position, (20, 40))  # Default to "Top Left" if position is not recognized
            
            # Adding text with transparency
            cv2.putText(overlay, text, pos, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
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
                # Set the sample rate to 48kHz
                audio.write_audiofile(audio_output_path, fps=48000)

            messagebox.showinfo("Success", f"Audio extracted successfully to {audio_output_path}!")
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = VideoCutterApp(root)
    root.mainloop()
