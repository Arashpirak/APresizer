
from PIL import Image
import os
import shutil
import tkinter as tk
import sys
from tkinter import messagebox, filedialog
import pygame

# Function to resize an image based on a maximum size (in KB)
def resize_image(input_path, output_path, filename, max_size_kb=100, suffix="_resized"):
    global total_resized
    try:
        with Image.open(input_path) as img:
            root.update_idletasks() # Update UI to ensure smooth interface 
            warning_label.config(text="----------------------------------------------------------------------------------------------------------------------------------", fg="red") # clear the label
            warning_label.config(text=f"👨‍💻Working on {filename}", fg="blue") # Update user on current file being processed
            root.update_idletasks()

            width, height = img.size  # Get original image dimensions
            size_kb = os.path.getsize(input_path) / 1024  # Get the image size in KB
            # Prevent resizing if input and output paths are the same
            if os.path.abspath(input_path) == os.path.abspath(output_path):
                warning_label.config(text="👨‍💻Source and destination are the same file . Skipping...", fg="orange")
                play_warning_sound()
                return False
            # If image size is already smaller than the target, just copy it (could add the suffix) 
            if size_kb <= max_size_kb:
                # filename = append_suffix(filename, suffix)# Add suffix to the filename
                new_output_path = os.path.join(os.path.dirname(output_path), filename)
                shutil.copy(input_path, new_output_path)
                small_image()  # Alert user for same size images
                return True
            
            
            temp_output_path = "temp_" + os.path.basename(output_path)
            ratio = 1.0 # Start with the original size ratio
            i = 0
            # Resize iteratively until the image meets the size requirement
            while not max_size_kb * 0.8 < size_kb <= max_size_kb:
                i +=1
                dif_size = size_kb - max_size_kb  # Calculate the difference in size
                g_rate = dif_size / max_size_kb  # Determine how much bigger the file is
                
                # Adjust the ratio based on the size difference
                if  g_rate > 1.25: # check if size is big enough
                    ratio *= 1 / (g_rate ** (1/2))  # reduces ratio based on the size difference
                else:
                    ratio *= 0.90 # Reduce just by 10% each iteration if g_rate is small

                # Resize the image
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                img_resized.save(temp_output_path, optimize=True, quality=85)  # Save resized image temporarily
                size_kb = os.path.getsize(temp_output_path) / 1024  # Get the new size in KB

                # Check if size is now within the limit
                if size_kb <= max_size_kb:
                    if max_size_kb * 0.8 < size_kb <= max_size_kb:
                        new_filename = append_suffix(filename, suffix)  # Add suffix to new filename
                        new_output_path = os.path.join(os.path.dirname(output_path), new_filename)
                        shutil.move(temp_output_path, new_output_path)  # Move resized image to final location
                        total_resized += 1  # Increment the count of resized images
                        return True
                    else:
                        ratio *= max_size_kb / (size_kb) # Further adjust the ratio if lower than the size limit 
            
        # Remove temp file after processing
        os.remove(temp_output_path)
        warning_label_2.config(text=f"👨‍💻Failed to resize {filename} to under {max_size_kb} KB", fg="orange")
        play_warning_sound()
    

    except Exception as e:
        play_warningRed_sound()  # Play red alert sound on exception
        messagebox.showerror("Error", f"Failed to resize {filename}: {str(e)}")
        warning_label_2.config(text=f"Failed to resize {filename}", fg="red")
        warning_label.config(text="-----------------------------------------------------------", fg="Black")
        return False
    
# Function to append a suffix to the filename (e.g., _resized)
def append_suffix(filename, suffix):
    name, ext = os.path.splitext(filename)
    return f"{name}{suffix}{ext}"

# Function to count and alert user small images that don't need resizing
def small_image():
    global total_not_resized
    total_not_resized += 1  # Increment count of images that don't need resizing
    warning_label_2.config(text=f"💻 {total_not_resized} images were small enough", fg="orange")
    play_warning_sound()

# Function to resize all images in a directory
def resize_images_in_directory(input_dir, output_dir, max_size_kb=100):
    global warning_label, warning_label_2

    # Check if the input directory is empty
    if not os.listdir(input_dir):
        warning_label.config(text="💻ERROR: The input directory is empty of images.", fg="red")
        play_warningRed_sound()
        return False
    
    # Iterate through all files in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):  # Only resize image files
            if not os.path.exists(output_dir):# creat output folder if in the middle of resizing was removed
                os.makedirs(output_dir)
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            warning_label.config(text="----------------------------------------------------------------------------------------------------------------------------------", fg="red") # clear the label
             # Resize the image
            if not resize_image(input_path, output_path, filename, max_size_kb):
                warning_label_2.config(text=f"Could not resize {filename}", fg="red")
                warning_label.config(text="-----------------------------------------------------------", fg="Black")
                play_warning_sound()

    return True

# Function to start resizing process when user clicks "Start Resizing"
def start_resizing():
    warning_label.config(text=f"--------------------------------------------------------------------------", fg="black") # clear the label
    warning_label_2.config(text=f"------------------------------------------------------------------------", fg="black") # clear the label
    
    global total_resized, total_not_resized
    try:
        root.update_idletasks()  # Ensure UI stays responsive

        items = input_dir.get().split(", ")  # Get input paths (files/folders)

        try:
            max_size_kb = int(size_entry.get())
            if max_size_kb < 1:
                warning_label.config(text="💻 Your Number < 1  !", fg="red")
                play_warningRed_sound()
                return

        except ValueError:
            warning_label.config(text="💻Please enter a valid number for size.", fg="red")
            play_warningRed_sound()
            return
        
        play_background_music()  # Start background music during resizing

        # Process each item in the input (file or folder)
        for item in items:
            if os.path.isfile(item):
                filename = os.path.basename(item)
                input_address = os.path.dirname(item)
                output_dir = os.path.join(input_address, "Resized")  # Create "Resized" folder for output
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_path = os.path.join(output_dir, filename)
                warning_label.config(text="----------------------------------------------------------------------------------------------------------------------------------", fg="black") # clear label
                    
                if resize_image(item, output_path, filename, max_size_kb):
                    root.update_idletasks() # do nothing
                else:
                    warning_label_2.config(text=f"💻Could not resize {filename}", fg="red")
                    play_warning_sound()
            elif os.path.isdir(item):
                
                # Get all files in the directory and check if there are any supported image files
                has_image = any(filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')) for filename in os.listdir(item))
                    
                if not has_image:
                    
                    warning_label.config(text=f"💻The folder does not contain any image !", fg="red")
                    play_warningRed_sound()
                    return

                if not os.listdir(item):  # Check if directory is empty
                    warning_label.config(text=f"The folder is empty.", fg="red")
                    play_warningRed_sound()
                    return
                else:
                    output_dir = os.path.join(item, "Resized")  # Create "Resized" folder inside the directory
                    if not os.path.exists(output_dir):
                        os.makedirs(output_dir)
                if resize_images_in_directory(item, output_dir, max_size_kb):
                    warning_label.config(text=f"Successfully {total_resized + total_not_resized} images Saved in (Resized) Folder .\n{total_resized} images Resized and {total_not_resized} images with same size ", fg="green")
                    warning_label_2.config(text=f"💻Done", fg="blue")
                    play_Done_music()  # Play success and Finish sound
                else:
                    warning_label.config(text="💻Error processing directory", fg="red")
                    play_warningRed_sound()
                    return
            else:
                dynamic_label.config(text="💻Invalid files or directories !", fg="red")
                warning_label.config(text="--------------", fg="black")
                play_warningRed_sound()
                return
                
        warning_label.config(text=f" {total_resized + total_not_resized} images Saved in (Resized) Folder .\n{total_resized} images Resized and {total_not_resized} images with same size ", fg="green")
        warning_label_2.config(text=f"💻Done", fg="blue")
        play_Done_music()
        
        
        #reset numbers for next try
        total_resized = 0
        total_not_resized = 0

    except Exception as e:
        play_warningRed_sound()
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        warning_label.config(text="An error occurred.", fg="red")

def choose_files():
    # Open a file dialog to select multiple image files
    files = filedialog.askopenfilenames(title="Choose files", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
    # If a folder is selected, update the input_dir variable and display the folder path
    if files:
        input_dir.set(", ".join(files))  # Store the selected folder path
          # Update the label to show the chosen folder
        dynamic_label.config(text=f"\nChosen files: {', '.join(os.path.basename(f) for f in files)}", fg="gray")

def choose_folder():
    folder = filedialog.askdirectory(title="Choose a folder")
    if folder:
        input_dir.set(folder)
        dynamic_label.config(text=f"\nChosen folder: {folder}", fg="gray")

def get_base_path():# Check if the program is running in a PyInstaller environment
    # If so, return the base path for resources; otherwise, return the current directory
    return sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")

def play_music(file_name, loops=0):
    # Initialize pygame mixer if not already initialized
    pygame.mixer.init()
    # Get the full path to the music file and play it
    music_path = os.path.join(get_base_path(), file_name)
    pygame.mixer.music.load(music_path)
    pygame.mixer.music.play(loops=loops)

def play_warning_sound():# Play a warning sound using a separate channel to avoid interrupting other sounds
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    sound_path = os.path.join(get_base_path(), "warning.mp3")
    warning_sound = pygame.mixer.Sound(sound_path)
    warning_channel = pygame.mixer.Channel(1)  # Use channel 1 for warning sounds
    warning_channel.play(warning_sound)

# Simplified function calls
def play_background_music():
    play_music("keyboard-typing.mp3", loops=-1)# Play background typing sound on loop during the resizing process

def play_Done_music():# Play sound when resizing is done
    play_music("Alarm07 (mp3cut.net).wav", loops=1)

def play_warningRed_sound():# Play a red warning sound for critical errors
    play_music("chord.wav", loops=1)

def play_welcome_music():# Play a welcome sound when the app starts
    play_music("harp_welcome.mp3", loops=0)

# Initialize counters for resized and non-resized images
global total_resized, total_not_resized
total_resized = 0
total_not_resized = 0

if __name__ == "__main__":
    # Set up the main window for the GUI application
    root = tk.Tk()
    root.title("👨‍💻AP Image Resizer")
    root.geometry("500x400")

    # Initialize StringVar to hold the selected file or folder paths
    input_dir = tk.StringVar()
    input_dir.set("Not chosen")

    # Display a welcome label
    static_label = tk.Label(root, text="Welcome", fg="blue", font=("Arial",19))
    static_label.pack(pady=5)

    # Button to choose image files
    choose_files_button = tk.Button(root, text="📄Choose Images", command=choose_files)
    choose_files_button.pack(pady=8)

    # Button to choose a folder containing images
    choose_folder_button = tk.Button(root, text="📂 Choose Folder", command=choose_folder)
    choose_folder_button.pack(pady=8)

    # Label to display the chosen files or folder dynamically
    dynamic_label = tk.Label(root, text="⬆️➡️💻", fg="red")
    dynamic_label.pack(pady=5)

    # Prompt for the user to enter the maximum image size in KB
    tk.Label(root, text="Enter the maximum size for images in KB:", font=("Arial",10)).pack()
    size_entry = tk.Entry(root, width=10)
    size_entry.pack(pady=12)

    # Button to start the resizing process
    start_button = tk.Button(root, text="Start Resizing", font=("Arial",10), command=start_resizing)
    start_button.pack(pady=7)

    # Play the welcome sound when the app starts
    play_welcome_music()

    # Label to display warnings and progress updates
    warning_label = tk.Label(root, text="", fg="red")
    warning_label.pack(pady=7)

    warning_label_2 = tk.Label(root, text="", fg="blue")
    warning_label_2.pack(pady=(10,10))

    # Start the main loop for the GUI
    root.mainloop()
