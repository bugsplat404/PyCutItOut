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

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4;*.avi;*.mov")])
    if file_path:
        input_file_entry.delete(0, tk.END)
        input_file_entry.insert(0, file_path)
        with VideoFileClip(file_path) as video:
            duration = int(video.duration)
            end_time_var.set(duration)

def select_audio_file():
    file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3;*.wav")])
    if file_path:
        audio_file_entry.delete(0, tk.END)
        audio_file_entry.insert(0, file_path)

def cut_video():
    input_file = input_file_entry.get()
    audio_file = audio_file_entry.get()
    if not input_file:
        messagebox.showerror("Error", "Please select a video file.")
        return

    try:
        start_time = int(start_time_entry.get())
        end_time = int(end_time_entry.get())
        width = int(width_entry.get())
        height = int(height_entry.get())
        video_volume = float(video_volume_var.get())
        audio_volume = float(audio_volume_var.get())
    except ValueError:
        messagebox.showerror("Error", "Start time, end time, width, height, and volume must be integers or floats.")
        return

    if start_time >= end_time:
        messagebox.showerror("Error", "End time must be greater than start time.")
        return

    output_dir = filedialog.askdirectory()
    if not output_dir:
        return

    def process_video():
        progress_bar.start()

        try:
            with VideoFileClip(input_file) as video:
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

                if audio_file:
                    with AudioFileClip(audio_file) as new_audio:
                        new_audio = new_audio.volumex(audio_volume)
                        composite_audio = CompositeAudioClip([subclip.audio, new_audio])
                        subclip = subclip.set_audio(composite_audio)

                output_file = os.path.join(output_dir, f"cut_video_{start_time}_{end_time}.mp4")
                subclip.write_videofile(output_file, codec="libx264")

            progress_bar.stop()
            messagebox.showinfo("Success", "Video cut and audio added successfully!")
        except Exception as e:
            progress_bar.stop()
            messagebox.showerror("Error", str(e))
        finally:
            progress_var.set(100)

    threading.Thread(target=process_video).start()

def update_video_volume_label(value):
    video_volume_label.config(text=f"Video Volume: {float(value):.1f}")

def update_audio_volume_label(value):
    audio_volume_label.config(text=f"Audio Volume: {float(value):.1f}")

# Set up the GUI
root = ttk.Window(themename="superhero")
root.title("Video Cutter")

ttk.Label(root, text="Input Video File:").grid(row=0, column=0, padx=10, pady=10)
input_file_entry = ttk.Entry(root, width=50)
input_file_entry.grid(row=0, column=1, padx=10, pady=10)
ttk.Button(root, text="Browse", command=select_file, bootstyle="primary").grid(row=0, column=2, padx=10, pady=10)

ttk.Label(root, text="Input Audio File (optional):").grid(row=1, column=0, padx=10, pady=10)
audio_file_entry = ttk.Entry(root, width=50)
audio_file_entry.grid(row=1, column=1, padx=10, pady=10)
ttk.Button(root, text="Browse", command=select_audio_file, bootstyle="primary").grid(row=1, column=2, padx=10, pady=10)

ttk.Label(root, text="Start Time (seconds):").grid(row=2, column=0, padx=10, pady=10)
start_time_var = tk.IntVar(value=0)
start_time_entry = ttk.Entry(root, textvariable=start_time_var)
start_time_entry.grid(row=2, column=1, padx=10, pady=10)

ttk.Label(root, text="End Time (seconds):").grid(row=3, column=0, padx=10, pady=10)
end_time_var = tk.IntVar(value=60)
end_time_entry = ttk.Entry(root, textvariable=end_time_var)
end_time_entry.grid(row=3, column=1, padx=10, pady=10)

ttk.Label(root, text="Width:").grid(row=4, column=0, padx=10, pady=10)
width_var = tk.IntVar(value=1920)
width_entry = ttk.Entry(root, textvariable=width_var)
width_entry.grid(row=4, column=1, padx=10, pady=10)

ttk.Label(root, text="Height:").grid(row=5, column=0, padx=10, pady=10)
height_var = tk.IntVar(value=1080)
height_entry = ttk.Entry(root, textvariable=height_var)
height_entry.grid(row=5, column=1, padx=10, pady=10)

video_volume_label = ttk.Label(root, text="Video Volume: 1.0")
video_volume_label.grid(row=6, column=0, padx=10, pady=10)
video_volume_var = tk.DoubleVar(value=1.0)
video_volume_slider = ttk.Scale(root, from_=0, to=2, orient=tk.HORIZONTAL, variable=video_volume_var, command=update_video_volume_label)
video_volume_slider.grid(row=6, column=1, padx=10, pady=10)

audio_volume_label = ttk.Label(root, text="Audio Volume: 1.0")
audio_volume_label.grid(row=7, column=0, padx=10, pady=10)
audio_volume_var = tk.DoubleVar(value=1.0)
audio_volume_slider = ttk.Scale(root, from_=0, to=2, orient=tk.HORIZONTAL, variable=audio_volume_var, command=update_audio_volume_label)
audio_volume_slider.grid(row=7, column=1, padx=10, pady=10)

ttk.Button(root, text="Cut Video", command=cut_video, bootstyle="success").grid(row=8, column=0, columnspan=3, pady=20)

progress_var = tk.IntVar()
progress_bar = ttk.Progressbar(root, orient=tk.HORIZONTAL, length=400, mode='indeterminate', variable=progress_var)
progress_bar.grid(row=9, column=0, columnspan=3, padx=10, pady=10)

root.mainloop()
