from os import path
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

MS = 33 # Medium psnr number
S = 27 # Small psnr number
SS = 22 # Super Small psnr number
newfolder = 0 # Do not save images to a new folder
max_psnrsize_kb = 1000 # Resize images larger than 1MB for faster PSNR calculation  
# Ftex = 0 # Enable this to save a FindTexes image (currently disabled)
# Global variable to track mute state
is_muted = False

def resize_psnr(input_path, filename, output_dir): 
    from skimage.metrics import peak_signal_noise_ratio as psnr
    from PIL import Image
    from numpy import array, stack, uint8
    from skimage import transform

    # Global variables
    global ratio, total_resized, good_psnr_value, original_psnr,max_psnrsize_kb, Ftex

    size_kb = path.getsize(input_path) / 1024
    
    if size_kb >= max_psnrsize_kb: # Resize images larger than 1MB for faster PSNR calculation
        resize_image(input_path, output_dir, filename,"_resized", 1)
        return True

    

    # Determine suffix based on PSNR value
    if good_psnr_value == MS:
        suffix = "_Medium.jpg"
    elif good_psnr_value == S:
        suffix = "_Small.jpg"
    elif good_psnr_value == SS:
        suffix = "_SuperSmall.jpg"
        
    output_path = path.join(output_dir, filename)
    
    # Initialize PSNR and ratio
    original_psnr = good_psnr_value
    ratio = 1

    # Define output filenames
    resized_filename = path.splitext(output_path)[0] + suffix
    resized_finedtexes = path.splitext(output_path)[0] + "Fnd-" + suffix

    try:
        # Update GUI
        update_warning_message(warning_label, f"Working on {filename}", "blue")
        
        # Open and process the image
        original = Image.open(input_path)
        original_np = array(original)  # Convert to NumPy array
        
        # Ensure correct image format
        if len(original_np.shape) == 2:  # Grayscale image
            original_np = stack((original_np,) * 3, axis=-1)  # Convert to RGB format
        elif original_np.shape[2] == 4:  # RGBA image
            original_np = original_np[:, :, :3]  # Convert to RGB
        
        i = 0
        while True:
            i += 1  # Counter to prevent excessive resizing
            update_warning_message(warning_label_2, f"processing on {filename}  {round((i/8)*100)} %", "blue")
            
            # Calculate new dimensions
            new_height = int(original_np.shape[0] * ratio)
            new_width = int(original_np.shape[1] * ratio)

            def adjust_psnr_if_too_small(good_psnr_value):
                if good_psnr_value == SS:
                    return S
                elif good_psnr_value == S:
                    return MS
                return good_psnr_value
            # Check if image is too small
            if new_width < 2 or new_height < 2:
                warning_label.config(text="Sorry, this image can't be this small! (increased to a bigger size)", fg="red")
                play_warning_sound()
                good_psnr_value = adjust_psnr_if_too_small(good_psnr_value)
                new_height, new_width = original_np.shape[0], original_np.shape[1]
                ratio = 1

            # Resize image
            resized_ratio = transform.resize(original_np, (new_height, new_width), anti_aliasing=True)
            
            # Resize back to original dimensions to calculate PSNR
            resized_back = transform.resize(resized_ratio, (original_np.shape[0], original_np.shape[1]), anti_aliasing=True)
            resized_back_uint8 = (resized_back * 255).astype(uint8)
            
            # Calculate PSNR
            psnr_value = psnr(original_np, resized_back_uint8, data_range=255)

            # Calculate PSNR difference and adjustment rates
            dif_psnr = psnr_value - good_psnr_value
            improvedDifPsnr = dif_psnr + (10 - dif_psnr)*0.5
            g_rate = dif_psnr / good_psnr_value
            improveg_rate = (improvedDifPsnr)  / good_psnr_value
            
            # Adjust ratio based on PSNR difference
            if g_rate > 0.1:
                ratio *= 1 / ((1 + improveg_rate) ** 2.2)
            elif psnr_value > good_psnr_value * 1.1:
                ratio *= 0.85  # Slightly reduce ratio
            
            # Check if PSNR is within acceptable range
            if psnr_value >= good_psnr_value and psnr_value <= good_psnr_value * 1.1 or i > 8:
                i = 0
                update_warning_message(warning_label_2, f"processing on {filename} 100 %", "blue")
                resizedratio_uint8 = (resized_ratio * 255).astype(uint8)
                resizedratio_pil = Image.fromarray(resizedratio_uint8)
                resizedratio_pil.save(resized_filename, "JPEG", quality=85)

                # Apply text detection if Ftex is True
                # if Ftex == 1: # This part is used when text detection is required.
                #     compressed_resized_pil = Texes(resized_filename,original_np, ratio)
                #     compressed_resized_pil.save(resized_finedtexes, "JPEG", quality=50)  # Save with quality 50

                total_resized += 1
                return True

            elif psnr_value < good_psnr_value:
                # Increase ratio if PSNR is low
                dif_good = good_psnr_value - psnr_value
                ImprovedGoodDif = dif_good+(dif_good / (1 + dif_good ** 5))
                ratio *= 1 / ((psnr_value / (good_psnr_value ** (1 + (3 * (ImprovedGoodDif / good_psnr_value))) )* (1 - ratio)) + ratio)

    except Exception as e:
        # Handle errors
        play_warningRed_sound()
        messagebox.showerror("Error", f"Failed to resize {filename}: {str(e)}")
        warning_label_2.config(text=f"Failed to resize {filename}", fg="red")
        warning_label.config(text="-----------------------------------------------------------", fg="Black")
        return False

            

def resize_image(input_path, output_dir, filename, suffix="_resized",psnr=0):
    
    from os import remove 
    import shutil
    from PIL import Image
    
    
    global total_resized, good_psnr_value,Ftex
    if psnr == 1:
        max_size_kb = max_psnrsize_kb
    try:    
        if good_psnr_value == 0:
            max_size_kb = int(size_entry.get())
            if max_size_kb < 1:
                update_warning_message(warning_label, " Your Number < 1 !", "red")
                play_warningRed_sound()
                return 
        
        else:
            good_psnr_value = good_psnr_value
    except ValueError:
        update_warning_message(warning_label, "Please enter a valid number for size.", "red")
        play_warningRed_sound()
        return
    
    if psnr == 1:
        max_size_kb == max_psnrsize_kb

    try:
        with Image.open(input_path) as img:
           
            update_warning_message(warning_label, f"Working on {filename}", "blue")
            width, height = img.size
            size_kb = path.getsize(input_path) / 1024
            new_filename = append_suffix(filename, suffix)# Add suffix to the filename
            output_path = path.join(output_dir, new_filename)

            if path.abspath(input_path) == path.abspath(output_path):
                update_warning_message(warning_label, "👨‍💻Source and destination are the same file . Skipping...", "orange")
                play_warning_sound()
                return False

            
            if size_kb <= max_size_kb:
                new_filename = append_suffix(filename, suffix)# Add suffix to the filename
                new_output_path = path.join(path.dirname(output_path), new_filename)
                shutil.copy(input_path, new_output_path)
                small_image(filename)
                return True
            
            temp_output_path = "temp_" + path.basename(output_path)
            ratio = 1.0
            i = 0

            
            while not max_size_kb * 0.8 < size_kb <= max_size_kb:
                i +=1
                dif_size = size_kb - max_size_kb 
                g_rate = dif_size / max_size_kb
                
                if  g_rate > 1.25: # Set g_rate to ensure the ratio is less than 0.90.
                    ratio *= 1 / (g_rate ** (1/2)) 
                else:
                    ratio *= 0.90

                new_width = int(width * ratio)
                new_height = int(height * ratio)
                img_resized = img.resize((new_width, new_height), Image.LANCZOS)
                img_resized.save(temp_output_path, optimize=True, quality=85)
                size_kb = path.getsize(temp_output_path) / 1024
                if size_kb <= max_size_kb:
                    if max_size_kb * 0.8 < size_kb <= max_size_kb:
                        if psnr == 1:
                            resize_psnr(temp_output_path,filename,output_dir)
                            remove(temp_output_path)
                            return True

                        new_filename = append_suffix(filename, suffix)
                        new_output_path = path.join(path.dirname(output_path), new_filename)
                        shutil.move(temp_output_path, new_output_path)
                        # if Ftex == 1: # This part is used when text detection is required.
                        #     img_np = array(img)
                        #     compressed_resized_pil = Texes(new_output_path, img_np, ratio)
                        #     output_path = path.join(output_dir, filename)
                        #     resized_finedtexes = path.splitext(output_path)[0] + "Fnd" + suffix + ".jpg"
                        #     compressed_resized_pil.save(resized_finedtexes, "JPEG", quality=50)  # Save with quality 50
                        total_resized += 1
                        return True
                    else:
                        ratio *= max_size_kb / (size_kb)

        remove(temp_output_path)
        update_warning_message(warning_label, f"Failed to resize {filename} to under {max_size_kb} KB", "red")
        play_warning_sound()

    except Exception as e:
        play_warningRed_sound()
        messagebox.showerror("Error", f"Failed to resize {filename}: {str(e)}")
        update_warning_message(warning_label_2, f"Failed to resize {filename}", "red")
        update_warning_message(warning_label, "-----------------------------------------------------------", "Black")
        return False




# def Texes(resized_filename, original_np, ratio): # This part is used when text detection is required.
#     from cv2 import imread, cvtColor, rectangle
#     from cv2 import COLOR_RGB2GRAY, COLOR_BGR2RGB
#     import sys
#     from os import remove, path 
#     import pytesseract
#     # Construct the path to tesseract.exe
#     # if getattr(sys, 'frozen', False):
#     #     app_directory = path.join(sys._MEIPASS)
#     # else:   
#     #     app_directory = path.join(path.dirname(path.abspath(__file__)))

#     # tesseract_path = path.join(get_base_path(), "tesseract.exe")
#     # tesseract_path = path.join(app_directory, "Tesseract-OCR", "tesseract.exe")
#     # pytesseract.pytesseract.tesseract_cmd = tesseract_path
#     import pytesseract
#     from PIL import Image
#     from numpy import where, array, ones, uint8
#     from io import BytesIO
#     # app_location = path.dirname(sys.executable)

#     try:
#         resizededited = imread(resized_filename)
#         # Convert to RGB to maintain consistency with original images
#         resizededited = cvtColor(resizededited, COLOR_BGR2RGB)
#         height, width, _ = resizededited.shape
#         # Convert to grayscale for text detection
#         gray_image = cvtColor(original_np, COLOR_RGB2GRAY)

#         # Use Tesseract to obtain bounding box details of text
#         data = pytesseract.image_to_data(gray_image, lang='eng+fas', output_type= pytesseract.Output.DICT)

#         # Create a mask for non-text areas
#         mask =ones(resizededited.shape[:2], dtype=uint8) * 255
#         remove(resized_filename)
#         # Mark text regions in the mask
#         n_boxes = len(data['text'])
#         contour = False
#         for i in range(n_boxes):
#             if int(data['conf'][i]) > 50:  # Confidence threshold
#                 (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
#                 xratio = round(x * ratio)
#                 yratio = round(y * ratio)
#                 wratio = round(w * ratio)
#                 hratio = round(h * ratio)
#                 if hratio > (height / 2) or wratio > (width / 2):# check if the selection area is not normal
#                     continue
#                 contour = True
#                 # image = rectangle(resizededited, (xratio, yratio), (xratio + wratio, yratio + hratio), (0, 255, 0), 0)
#                 # print("founding")
#                 # print(f"Detected Text: {data['text'][i]}")
#                 # print(f"Location: ({x}, {y}), Width: {w}, Height: {h}\n")
#                 mask[yratio:yratio+hratio, xratio:xratio+wratio] = 0  # Mask text areas
#         # Apply compression to non-text areas
#         def compress_non_text_area(region, mask_region, quality):
#             pil_image = Image.fromarray(region)
#             # Compress the image
#             img_byte_arr = BytesIO()
#             pil_image.save(img_byte_arr, format='JPEG', quality=quality)
#             img_byte_arr = img_byte_arr.getvalue()  # Retrieve byte data from BytesIO
#             compressed_image = array(Image.open(BytesIO(img_byte_arr)))
#             # compressed_image = cv.cvtColor(compressed_image, cv.COLOR_BGR2RGB)
#             final_image = where(mask_region[..., None] == 0, region, compressed_image)
#             return final_image
#         # Compress non-text areas and resize the image
#         if contour:
#             # compressed_resized_image = compress_non_text_area(image, mask, quality=35) # quality of non important parts
#             compressed_resized_image = compress_non_text_area(resizededited, mask, quality=35) # quality of non important parts
#         else:
#             compressed_resized_image = compress_non_text_area(resizededited, mask, quality=35) # quality of non important parts

#         # Save the final compressed and resized image
#         compressed_resized_pil = Image.fromarray(compressed_resized_image)
#         return compressed_resized_pil
#     except Exception as e:
#             play_warningRed_sound()
#             messagebox.showerror("Error", f"Failed to Find Texes: {str(e)}")
#             update_warning_message(warning_label_2, "Failed to Find Texes", "red")
#             update_warning_message(warning_label, "-----------------------------------------------------------", "Black")
#             return False
        

def append_suffix(filename, suffix):
    name, ext = path.splitext(filename)
    return f"{name}{suffix}{ext}"

def small_image(filename):
    global total_not_resized
    total_not_resized += 1
    update_warning_message(warning_label_2, f" {total_not_resized} images were small enough", "orange")
    play_warning_sound()

def resize_images_in_directory(input_dir, output_dir):
    from os import listdir
    global warning_label, warning_label_2, good_psnr_value,original_psnr

    if not listdir(input_dir):
        update_warning_message(warning_label, "ERROR: The input directory is empty of images.", "red")
        play_warningRed_sound()
        return False

    for filename in listdir(input_dir):
        if filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')):
            input_path = path.join(input_dir, filename)
            if good_psnr_value == 0:# check if user has entered the size
                if not resize_image(input_path, output_dir, filename):
                    update_warning_message(warning_label_2, f"Could not resize {filename}", "red")
                    update_warning_message(warning_label, "-----------------------------------------------------------", "Black")
                    play_warning_sound()
                    return False
            else:
                if not resize_psnr(input_path, filename, output_dir): 
                    update_warning_message(warning_label_2, f"Could not resize {filename}", "red")
                    update_warning_message(warning_label, "-----------------------------------------------------------", "Black")
                    play_warning_sound()
                    return False
                good_psnr_value = original_psnr #update good psnr value
    return True

def doNothing():
    pass

def start_resizing():
    from os import listdir, makedirs
    warning_label_2.config(text=f"-------------------------------------")
    
    
    global total_resized, total_not_resized, good_psnr_value, newfolder,original_psnr

    try:
        root.update_idletasks()

        items = input_dir.get().split(", ")  

        
        
        play_background_music()

        for item in items:
            input_address = path.dirname(item)
            filename = path.basename(item)
            if path.isfile(item): 
                
                if newfolder == 1:
                    output_dir = path.join(input_address, "Resized")
                    if not path.exists(output_dir):
                        makedirs(output_dir)
                else:
                    output_dir = input_address
                warning_label.config(text="----------------------------------------------------------------------------------------------------------------------------------", fg="black") # clear label
                
                if good_psnr_value == 0:# check if user has entered the size value
                    if resize_image(item, output_dir, filename):
                        root.update_idletasks() # do nothing)
                    else:
                        warning_label_2.config(text=f"Could not resize {filename}", fg="red")
                        play_warningRed_sound()
                        return
                else :
                    if resize_psnr(item, filename, output_dir):
                        good_psnr_value = original_psnr
                    else:
                        warning_label_2.config(text=f"Could not resize {filename}", fg="red")
                        play_warningRed_sound()
                        return
                            
            elif path.isdir(item):
                # Get all files in the directory and check if there are any supported image files
                has_image = any(filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'bmp')) for filename in listdir(item))
                    
                if not has_image:
                    warning_label.config(text=f"The folder does not contain any images .", fg="red")
                    play_warningRed_sound()
                    return
                if not listdir(item):  # Check if directory is empty
                    warning_label.config(text=f"The folder is empty.", fg="red")
                    play_warningRed_sound()
                    return
                else:
                    if newfolder == 1:
                        output_dir = path.join(item, "Resized")
                        if not path.exists(output_dir):
                            makedirs(output_dir)
                    else: 
                        output_dir = path.join(input_address,filename)

                if resize_images_in_directory(item, output_dir):
                    doNothing()
                    
                else:
                    warning_label.config(text="Error processing directory", fg="red")
                    play_warningRed_sound()
                    return
            
            else:
                warning_label.config(text="Invalid files or directories !", fg="red")
                warning_label_2.config(text="--------------", fg="red")
                play_warningRed_sound()
                return

        if newfolder == 1:
            update_warning_message(warning_label, f"Successfully {total_resized + total_not_resized} images Saved in (Resized) Folder.\n{total_resized} images Resized and {total_not_resized} images with same size ", "green")
        else:
            update_warning_message(warning_label, f"Successfully {total_resized + total_not_resized} images Saved.\n{total_resized} images Resized and {total_not_resized} images with same size ", "green")
        update_warning_message(warning_label_2, "Done","blue")
        play_Done_music()

        total_resized = 0
        total_not_resized = 0


    except Exception as e:
        play_warningRed_sound()
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        warning_label.config(text="An error occurred.", fg="red")

import threading

def start_resizing_thread():
    resize_thread = threading.Thread(target=start_resizing)
    resize_thread.daemon = True  # Ensure the thread will be killed when the program exits
    resize_thread.start()


def choose_files():
    files = filedialog.askopenfilenames(title="Choose files", filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
    if files:
        dynamic_label.config(text=f"\nNumber of selected files: {len(files)}")
        input_dir.set(", ".join(files))

def choose_folder():
    folder = filedialog.askdirectory(title="Choose a folder")
    if folder:
        input_dir.set(folder)
        dynamic_label.config(text=f"\nSelected folder: {folder}")

def get_base_path():# Check if the program is running in a PyInstaller environment
    import sys
    # If so, return the base path for resources; otherwise, return the current directory
    return sys._MEIPASS if hasattr(sys, '_MEIPASS') else path.abspath(".")

def play_music(file_name, loops=0):
    # Initialize pygame mixer if not already initialized
    mixer.init()
    # Get the full path to the music file and play it
    music_path = path.join(get_base_path(), file_name)
    mixer.music.load(music_path)
    mixer.music.play(loops=loops)

def play_warning_sound():# Play a warning sound using a separate channel to avoid interrupting other sounds
    if not mixer.get_init():
        mixer.init()
    sound_path = path.join(get_base_path(), "warning.mp3")
    warning_sound = mixer.Sound(sound_path)
    warning_channel = mixer.Channel(1)  # Use channel 1 for warning sounds
    warning_channel.play(warning_sound)

# Simplified function calls
def play_background_music():
    if not is_muted.get():  # Check mute state
        play_music("keyboard-typing.mp3", loops=-1)# Play background typing sound on loop during the resizing process

def play_Done_music():# Play sound when resizing is done
    play_music("Alarm07 (mp3cut.net).wav", loops=1)

def play_warningRed_sound():# Play a red warning sound for critical errors
    play_music("chord.wav", loops=1)

def play_welcome_music():# Play a welcome sound when the app starts
    play_music("harp_welcome.mp3", loops=0)

# Function to mute/unmute all sounds
def toggle_mute():
    # global is_muted
    # is_muted = not is_muted
    if is_muted.get():
        mixer.music.pause()  # Pause all background music
    else:
        mixer.music.unpause()  # Resume background music

def update_warning_message(label, message, color="red"):
    label.config(text=message, fg=color)
    root.update_idletasks()

global good_psnr_value
good_psnr_value = 0

def reset_button_styles():
    """Resets all the buttons to their default styles."""
    style.configure("Medium.TButton", font=("Arial", 12), background="SystemButtonFace", foreground="black")
    style.configure("Small.TButton", font=("Arial", 12), background="SystemButtonFace", foreground="black")
    style.configure("SuperSmall.TButton", font=("Arial", 12), background="SystemButtonFace", foreground="black")
    
    # Reset button styles
    Medium_button.config(style="Medium.TButton")
    Small_button.config(style="Small.TButton")
    Super_Small_button.config(style="SuperSmall.TButton")

def Medium_resizing():
    """Handles medium resizing logic and highlights the Medium button."""
    global good_psnr_value
    good_psnr_value = MS
    reset_button_styles()  # Reset all buttons
    
    # Highlight the Medium button
    style.configure("Medium.TButton", font=("Arial", 12, "bold"), background="lightgreen", foreground="blue")
    Medium_button.config(style="Medium.TButton")
    return good_psnr_value

def Small_resizing():
    """Handles small resizing logic and highlights the Small button."""
    global good_psnr_value
    good_psnr_value = S
    reset_button_styles()  # Reset all buttons
    
    # Highlight the Small button
    style.configure("Small.TButton", font=("Arial", 12, "bold"), background="lightgreen", foreground="blue")
    Small_button.config(style="Small.TButton")
    return good_psnr_value

def Super_Small_resizing():
    """Handles super small resizing logic and highlights the Super Small button."""
    global good_psnr_value
    good_psnr_value = SS
    reset_button_styles()  # Reset all buttons
    
    # Highlight the Super Small button
    style.configure("SuperSmall.TButton", font=("Arial", 12, "bold"), background="lightgreen", foreground="blue")
    Super_Small_button.config(style="SuperSmall.TButton")
    return good_psnr_value



def update_widgets():
    global good_psnr_value
    if size_var.get():
        # Show size entry and hide quality buttons
        size_label.place(x=140, y=130)  # Position the size label under the checkbox
        size_entry.place(x=215, y=165)  # Position the size entry under the label
        
        # Hide the quality buttons and the quality description
        Medium_button.place_forget()
        Small_button.place_forget()
        Super_Small_button.place_forget()
        quality_description.place_forget()
        good_psnr_value = 0

    else:
        # Show quality buttons and hide size entry
        Medium_button.place(x=50, y=165)
        Small_button.place(x=190, y=165)
        Super_Small_button.place(x=330, y=165)
        
        # Show the quality description
        quality_description.place(x=115, y=125)

        # Hide the size entry and the size description
        size_label.place_forget()
        size_entry.place_forget()
        
        
def newfoldermake():
    global newfolder
    
    if newf.get():
        newfolder = 1
    else:
        newfolder = 0

# def FindTexes():# This part is used when text detection is required.
#     global Ftex
#     if TFind.get():
#         Ftex = 1
#     else:
#         Ftex = 0

global total_resized, total_not_resized
total_resized = 0
total_not_resized = 0



def on_closing():
    # print("Window closed.")
    root.destroy()  # This will stop the Tkinter main loop and close the window
# Main GUI setup

if __name__ == "__main__":
    # Set up the main window for the GUI application
    root = tk.Tk()
    root.title("AP Image Resizer")
    root.geometry("500x450")

    # Set a background color
    root.configure(bg="#f0f0f0")

    # Custom style
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12), padding=5)
    style.configure("TLabel", font=("Arial", 12), background="#f0f0f0")
    style.configure("TEntry", padding=5)
    style.configure("FLabel.TLabel", foreground="Black", font=("Arial", 9))
    style.configure("BlueLabel.TLabel", foreground="blue", font=("Arial", 19))

    # Initialize StringVar to hold the selected file or folder paths
    input_dir = tk.StringVar()
    input_dir.set("Not chosen")

    # Display a welcome label
    static_label = ttk.Label(root, text="AP Image Resizer", style="BlueLabel.TLabel")
    static_label.place(x=150, y=15)

    # Button to choose image files
    choose_files_button = ttk.Button(root, text="Choose Images", command=choose_files)
    choose_files_button.place(x=72, y=55)

    # Label to display the chosen files or folder dynamically
    dynamic_label0 = ttk.Label(root, text="OR", style="TLabel")
    dynamic_label0.place(x=237, y=60)

    dynamic_label = ttk.Label(root, text="__", style="FLabel.TLabel")
    dynamic_label.pack(pady=90)

    # Button to choose a folder containing images
    choose_folder_button = ttk.Button(root, text=" Choose a Folder", command=choose_folder)
    choose_folder_button.place(x=290, y=55)


    # Prompt for the user to enter the maximum image size in KB
    size_label = ttk.Label(root, text="Enter the maximum size in KB:", style="TLabel")
    size_entry = ttk.Entry(root, width=10)
    size_label.place_forget()  # Hide initially
    size_entry.place_forget()  # Hide initially

    # Add a description for the quality buttons (shown by default)
    quality_description = ttk.Label(root, text="How much you want to Shrink images?", style="TLabel")
    quality_description.place(x=115, y=125)  # Visible by default


    # Buttons for different quality options (shown initially)
    Medium_button = ttk.Button(root, text="Medium", command=Medium_resizing)
    Small_button = ttk.Button(root, text="Small", command=Small_resizing)
    Super_Small_button = ttk.Button(root, text="Super Small", command=Super_Small_resizing)

    # Place these buttons initially
    Medium_button.place(x=50, y=165)
    Small_button.place(x=190, y=165)
    Super_Small_button.place(x=330, y=165)

    dynamic_label2 = ttk.Label(root, text="OR", style="TLabel").place(x=232, y=205)

    # Create a variable to track the checkbox state
    size_var = tk.BooleanVar()
    size_var.set(False)  # Default to showing quality buttons
    # Create a checkbox to select between size and quality
    ttk.Checkbutton(root, text="Enter your size manually", variable=size_var, command=update_widgets).place(x=175, y=230)

    # Create a variable to track the checkbox state
    newf = tk.BooleanVar()
    newf.set(False)  # Default to showing quality buttons
    ttk.Checkbutton(root, text="Paste resized images in a Newfolder", variable=newf, command=newfoldermake).place(x=50, y=255)


    # Create a variable to track the checkbox state
    is_muted = tk.BooleanVar()
    is_muted.set(False)  # Default to showing quality buttons
    ttk.Checkbutton(root, text="Mute Sound", variable=is_muted, command=toggle_mute).place(x=350, y=255)

    # Create a variable to track the checkbox state
    # TFind = tk.BooleanVar()
    # TFind.set(False)  # Default to showing quality buttons
    # ttk.Checkbutton(root, text="Find Texts", variable=TFind, command=FindTexes).place(x=335, y=230)

    # Button to start the resizing process
    start_button = ttk.Button(root, text="Start Resizing", command=start_resizing_thread)
    start_button.place(x=195, y=280)

    # Play the welcome sound when the app starts
    from pygame import mixer
    play_welcome_music()

    # Label to display warnings and progress updates
    warning_label = tk.Label(root, text="", fg="red")
    warning_label.pack(pady=(120, 30), anchor='n')  # Add 10 pixels of space above and 1 pixel below

    warning_label_2 = tk.Label(root, text=f"Running Location: {get_base_path()}", fg="blue")
    warning_label_2.pack(pady=(1, 1), anchor='n') 

    # Handle the window close event
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the main loop for the GUI
    root.mainloop()
