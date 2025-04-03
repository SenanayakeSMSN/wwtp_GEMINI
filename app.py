'''
import google.generativeai as genai
from PIL import Image
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
import time
from google.api_core import exceptions
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt (unchanged)
prompt = """
Analyze the provided image and determine if it depicts a wastewater treatment plant (WWTP). 
If it is a WWTP, provide a brief description of the scene and count the following:
- Number of circular features (e.g., tanks, clarifiers).
- Number of rectangular features (e.g., buildings, basins).
- Number of circular features with water (dark color).
- Number of circular features without water (light color).
- Number of rectangular features with water (dark color).
- Number of rectangular features without water (light color).
If it is not a WWTP, provide a brief description and set all counts to 0.
Provide your response in the following format:
- Is it a WWTP? [Yes/No]
- Description: [Brief description]
- Circular Features: [Number]
- Rectangular Features: [Number]
- Circular Features with Water: [Number]
- Circular Features without Water: [Number]
- Rectangular Features with Water: [Number]
- Rectangular Features without Water: [Number]
"""

# Function to analyze the image (unchanged)
def analyze_image(image_path, max_retries=3, rate_limit_delay=4):
    for attempt in range(max_retries):
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            response = model.generate_content([prompt, img])
            result_text = response.text.strip()
            
            lines = result_text.split('\n')
            is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
            description = "N/A"
            circular_count = 0
            rectangular_count = 0
            circular_with_water = 0
            circular_without_water = 0
            rectangular_with_water = 0
            rectangular_without_water = 0
            
            for line in lines:
                if "Description:" in line:
                    description = line.split('Description:')[1].strip()
                elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                    circular_count = int(line.split(':')[1].strip())
                elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                    rectangular_count = int(line.split(':')[1].strip())
                elif "Circular Features with Water:" in line:
                    circular_with_water = int(line.split(':')[1].strip())
                elif "Circular Features without Water:" in line:
                    circular_without_water = int(line.split(':')[1].strip())
                elif "Rectangular Features with Water:" in line:
                    rectangular_with_water = int(line.split(':')[1].strip())
                elif "Rectangular Features without Water:" in line:
                    rectangular_without_water = int(line.split(':')[1].strip())
            
            return {
                "Is WWTP?": is_wwtp,
                "Description": description,
                "Circular Features": circular_count,
                "Rectangular Features": rectangular_count,
                "Circular Features with Water": circular_with_water,
                "Circular Features without Water": circular_without_water,
                "Rectangular Features with Water": rectangular_with_water,
                "Rectangular Features without Water": rectangular_without_water
            }
        except exceptions.ResourceExhausted as e:
            if attempt < max_retries - 1:
                logger.warning(f"429 error for {image_path}, retrying in 10 seconds...")
                time.sleep(10)
            else:
                return {"Is WWTP?": "N/A", "Description": f"Error: {str(e)}", "Circular Features": 0, "Rectangular Features": 0, 
                        "Circular Features with Water": 0, "Circular Features without Water": 0, 
                        "Rectangular Features with Water": 0, "Rectangular Features without Water": 0}
        except Exception as e:
            if attempt == max_retries - 1:
                return {"Is WWTP?": "N/A", "Description": f"Error: {str(e)}", "Circular Features": 0, "Rectangular Features": 0, 
                        "Circular Features with Water": 0, "Circular Features without Water": 0, 
                        "Rectangular Features with Water": 0, "Rectangular Features without Water": 0}
            time.sleep(2)
    time.sleep(rate_limit_delay)

# Tkinter App
class WWTPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Image Analyzer")
        self.root.geometry("800x600")

        # Upload button
        self.upload_btn = tk.Button(root, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(pady=10)

        # Label for image path
        self.image_path_label = tk.Label(root, text="No image selected")
        self.image_path_label.pack(pady=5)

        # Analyze button
        self.analyze_btn = tk.Button(root, text="Analyze", command=self.analyze, state=tk.DISABLED)
        self.analyze_btn.pack(pady=10)

        # Canvas for text output
        self.canvas = tk.Canvas(root, width=600, height=400, bg="white")
        self.canvas.pack(pady=20)

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.tif *.tiff")])
        if file_path:
            self.image_path = file_path
            self.image_path_label.config(text=f"Selected: {os.path.basename(file_path)}")
            self.analyze_btn.config(state=tk.NORMAL)
            self.canvas.delete("all")  # Clear previous output

    def analyze(self):
        if not hasattr(self, 'image_path'):
            messagebox.showerror("Error", "Please upload an image first!")
            return
        
        self.canvas.delete("all")
        self.canvas.create_text(300, 200, text="Analyzing...", font=("Arial", 14))
        self.root.update()

        result = analyze_image(self.image_path)
        
        self.canvas.delete("all")
        if result["Is WWTP?"] == "Yes":
            self.display_simple_counts(result)
        elif result["Is WWTP?"] == "No":
            self.canvas.create_text(300, 200, text="This is not a WWTP.\n" + result["Description"], 
                                    font=("Arial", 14), justify="center")
        else:
            self.canvas.create_text(300, 200, text=result["Description"], font=("Arial", 14), justify="center")

    def display_simple_counts(self, result):
        # Display simplified output
        y_offset = 50
        self.canvas.create_text(300, y_offset, text=f"Circular objects with water - {result['Circular Features with Water']}", 
                                font=("Arial", 12), anchor="center")
        
        y_offset += 30
        self.canvas.create_text(300, y_offset, text=f"Circular objects without water - {result['Circular Features without Water']}", 
                                font=("Arial", 12), anchor="center")
        
        y_offset += 30
        self.canvas.create_text(300, y_offset, text=f"Rectangular objects with water - {result['Rectangular Features with Water']}", 
                                font=("Arial", 12), anchor="center")
        
        y_offset += 30
        self.canvas.create_text(300, y_offset, text=f"Rectangular objects without water - {result['Rectangular Features without Water']}", 
                                font=("Arial", 12), anchor="center")

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPApp(root)
    root.mainloop()

    
import tkinter as tk
from tkinter import filedialog, messagebox
import google.generativeai as genai
from PIL import Image
import os
import pandas as pd
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Updated prompt with stricter instructions
prompt = """
Analyze the provided image to determine if it depicts a wastewater treatment plant (WWTP). A WWTP is a system of interconnected units, not just isolated tanks. Use the following detailed guidelines to identify WWTP components and their arrangement, as their presence and logical layout are key to a positive identification:

*IDENTIFY WASTEWATER TREATMENT PLANT (WWTP) COMPONENTS:*

1.A. TANKS (Detailed Identification Rules):
   - Circular Tanks: Round structures made of concrete, steel, or other materials. Sizes vary greatly. Some may have covers or domes (appearing as solid circles), and some may have central mechanisms (e.g., rotating scraper arms). Count those with water (dark color) and without water (light color) separately.
   - Rectangular Tanks: Elongated basins, often with a length-to-width ratio of 3:1 to 5:1. They may appear singly, in groups, or in parallel series, sometimes with internal dividers or walls. Corners may not always be sharp. Count those with water (dark color) and without water (light color) separately.
   - Primary Sedimentation Tanks (PSTs): Predominantly circular and among the larger circular tanks. Look for a central mechanism (rotating scraper arm) and a darker central sludge hopper. Rectangular PSTs are less common but may have a longitudinal collector mechanism.

1.B. OTHER KEY WWTP INFRASTRUCTURE (Beyond Tanks):
   - Aeration Basins: Typically large rectangular basins, though circular or oval shapes are possible. Look for surface agitation (ripples, waves), visible aerators, or bubble patterns. Water may appear brownish due to microbial activity.
   - Clarifiers (Secondary Settling Tanks): Can be circular or rectangular, often downstream of aeration basins. Water may appear clearer than in PSTs. Circular clarifiers may have central mechanisms, potentially smaller than those in PSTs.
   - Sludge Drying Beds: Rectangular areas with clear divisions or rows. Look for drying sludge texture, changing from dark brown (wet) to lighter shades (dry). Often near settling tanks or clarifiers.
   - Inlet and Outlet Structures: Look for pipes, channels, or canals entering (from populated/industrial areas) and exiting (to a river, lake, or ocean). Pumping stations (small buildings) may be nearby.
   - Digesters: Tall, cylindrical tanks with conical bottoms or dome-shaped tops, often near sludge handling areas. A strong indicator if present.
   - Buildings: Administrative, laboratory, or equipment buildings. Support identification but are not definitive alone.

1.C. OVERALL LAYOUT AND INTERCONNECTEDNESS:
   - A functioning WWTP has a logical flow, e.g., Inlet -> PSTs -> Aeration Basins -> Clarifiers -> Outlet. Sludge handling (drying beds, digesters) is typically near PSTs and clarifiers. This spatial coherence strongly supports identification.

*INSTRUCTIONS:*
- If the image depicts a WWTP, provide a brief description of the scene and count the following:
  - Number of circular features (e.g., tanks, clarifiers).
  - Number of rectangular features (e.g., buildings, basins).
  - Number of circular features with water (dark color).
  - Number of circular features without water (light color).
  - Number of rectangular features with water (dark color).
  - Number of rectangular features without water (light color).
- If it is not a WWTP, provide a brief description and set all counts to 0.
- Use the provided guidelines to ensure accurate identification and differentiation of features.
- For all counts, provide only an integer value (e.g., 5, 10, 0). If exact counting is difficult due to resolution or overlapping features, estimate the number as an integer without additional text or qualifiers (e.g., use 20 instead of '20+' or '20 (approximate)').

*RESPONSE FORMAT:*
- Is it a WWTP? [Yes/No]
- Description: [Brief description]
- Circular Features: [Number]
- Rectangular Features: [Number]
- Circular Features with Water: [Number]
- Circular Features without Water: [Number]
- Rectangular Features with Water: [Number]
- Rectangular Features without Water: [Number]
"""

# List to store results
results = []

# Chatbot App
class WWTPChatBotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Chatbot Analyzer (Gemini)")
        self.root.geometry("800x600")
        self.image_path = None
        self.chat_history = []

        # Main frame
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Upload button
        self.upload_btn = tk.Button(self.main_frame, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(pady=5)

        # Image path label
        self.image_path_label = tk.Label(self.main_frame, text="No image selected")
        self.image_path_label.pack(pady=5)

        # Chat display
        self.chat_frame = tk.Frame(self.main_frame)
        self.chat_frame.pack(fill="both", expand=True, pady=5)
        
        self.chat_text = tk.Text(self.chat_frame, height=20, width=80, state="disabled")
        self.chat_text.pack(side="left", fill="both", expand=True)
        
        self.scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_text.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.chat_text.config(yscrollcommand=self.scrollbar.set)

        # Input frame
        self.input_frame = tk.Frame(self.main_frame)
        self.input_frame.pack(fill="x", pady=5)

        self.input_field = tk.Entry(self.input_frame, width=60)
        self.input_field.pack(side="left", padx=5)
        self.input_field.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_btn.pack(side="left")

        # Save results button
        self.save_btn = tk.Button(self.main_frame, text="Save Results", command=self.save_results)
        self.save_btn.pack(pady=5)

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.tif *.tiff")])
        if file_path:
            self.image_path = file_path
            self.image_path_label.config(text=f"Selected: {os.path.basename(file_path)}")
            self.add_to_chat("System", f"Image uploaded: {os.path.basename(file_path)}")
            # Perform initial WWTP analysis
            self.analyze_image(file_path, initial=True)

    def analyze_image(self, image_path, question=None, initial=False, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                content = [question if question else prompt, img]
                response = model.generate_content(content)
                result_text = response.text.strip()
                
                if initial:
                    # Parse initial WWTP analysis
                    lines = result_text.split('\n')
                    is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                    description = "N/A"
                    circular_count = rectangular_count = circular_with_water = circular_without_water = 0
                    rectangular_with_water = rectangular_without_water = 0
                    
                    def extract_number(text):
                        match = re.search(r'\d+', text)
                        return int(match.group()) if match else 0

                    for line in lines:
                        if "Description:" in line:
                            description = line.split('Description:')[1].strip()
                        elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                            circular_count = extract_number(line.split(':')[1].strip())
                        elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                            rectangular_count = extract_number(line.split(':')[1].strip())
                        elif "Circular Features with Water:" in line:
                            circular_with_water = extract_number(line.split(':')[1].strip())
                        elif "Circular Features without Water:" in line:
                            circular_without_water = extract_number(line.split(':')[1].strip())
                        elif "Rectangular Features with Water:" in line:
                            rectangular_with_water = extract_number(line.split(':')[1].strip())
                        elif "Rectangular Features without Water:" in line:
                            rectangular_without_water = extract_number(line.split(':')[1].strip())
                    
                    image_name = os.path.basename(image_path)
                    results.append({
                        "Image Name": image_name,
                        "Is WWTP?": is_wwtp,
                        "Num of Circular Features": circular_count,
                        "Num of Rectangular Features": rectangular_count,
                        "Num of Circular Features with Water": circular_with_water,
                        "Num of Circular Features without Water": circular_without_water,
                        "Num of Rectangular Features with Water": rectangular_with_water,
                        "Num of Rectangular Features without Water": rectangular_without_water,
                        "Description": description,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    self.add_to_chat("Gemini", result_text)
                else:
                    self.add_to_chat("Gemini", result_text)
                break

            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    logger.warning(f"429 error for {image_path}, retrying in 10 seconds...")
                    time.sleep(10)
                else:
                    error_msg = f"Error: {str(e)}"
                    self.add_to_chat("Gemini", error_msg)
                    if initial:
                        image_name = os.path.basename(image_path)
                        results.append({
                            "Image Name": image_name,
                            "Is WWTP?": "N/A",
                            "Num of Circular Features": 0,
                            "Num of Rectangular Features": 0,
                            "Num of Circular Features with Water": 0,
                            "Num of Circular Features without Water": 0,
                            "Num of Rectangular Features with Water": 0,
                            "Num of Rectangular Features without Water": 0,
                            "Description": error_msg,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
            except ValueError as e:
                error_msg = f"Error: Failed to parse response due to unexpected format - {str(e)}"
                self.add_to_chat("Gemini", error_msg)
                if initial:
                    image_name = os.path.basename(image_path)
                    results.append({
                        "Image Name": image_name,
                        "Is WWTP?": "N/A",
                        "Num of Circular Features": 0,
                        "Num of Rectangular Features": 0,
                        "Num of Circular Features with Water": 0,
                        "Num of Circular Features without Water": 0,
                        "Num of Rectangular Features with Water": 0,
                        "Num of Rectangular Features without Water": 0,
                        "Description": error_msg,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    error_msg = f"Error: {str(e)}"
                    self.add_to_chat("Gemini", error_msg)
                    if initial:
                        image_name = os.path.basename(image_path)
                        results.append({
                            "Image Name": image_name,
                            "Is WWTP?": "N/A",
                            "Num of Circular Features": 0,
                            "Num of Rectangular Features": 0,
                            "Num of Circular Features with Water": 0,
                            "Num of Circular Features without Water": 0,
                            "Num of Rectangular Features with Water": 0,
                            "Num of Rectangular Features without Water": 0,
                            "Description": error_msg,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                time.sleep(2)
        if not initial:
            time.sleep(rate_limit_delay)

    def send_message(self, event=None):
        message = self.input_field.get().strip()
        if not message:
            return
        
        self.add_to_chat("You", message)
        self.input_field.delete(0, tk.END)

        if not self.image_path:
            self.add_to_chat("Gemini", "Please upload an image first before asking questions!")
            return

        self.analyze_image(self.image_path, question=message)

    def add_to_chat(self, sender, message):
        self.chat_history.append(f"{sender}: {message}")
        self.chat_text.config(state="normal")
        self.chat_text.delete(1.0, tk.END)
        for line in self.chat_history:
            self.chat_text.insert(tk.END, line + "\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def save_results(self):
        if not results:
            messagebox.showinfo("Info", "No results to save yet!")
            return
        
        output_file = f"geminiallimagestest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)
        self.add_to_chat("System", f"Results saved to {output_file}")

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPChatBotApp(root)
    root.mainloop()
    

#process image folder
import google.generativeai as genai
from PIL import Image
import os
import pandas as pd
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt (same as original)
prompt = """
[Your original prompt remains unchanged here]
"""

class WWTPAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Image Analyzer")
        self.root.geometry("800x600")

        # Variables
        self.image_dir = tk.StringVar()
        self.results = []
        self.running = False

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # Directory selection
        tk.Label(self.root, text="Image Directory:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.image_dir, width=50).pack(pady=5)
        tk.Button(self.root, text="Browse", command=self.browse_directory).pack(pady=5)

        # Process button
        self.process_btn = tk.Button(self.root, text="Process Images", command=self.start_processing)
        self.process_btn.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=10)

        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.root, width=90, height=25)
        self.output_text.pack(pady=10)

        # Status label
        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            self.output_text.insert(tk.END, f"Selected directory: {directory}\n")

    def start_processing(self):
        if not self.image_dir.get():
            self.output_text.insert(tk.END, "Please select a directory first!\n")
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Process Images")
            return

        self.running = True
        self.process_btn.config(text="Stop Processing")
        self.results.clear()
        self.output_text.delete(1.0, tk.END)
        
        # Start processing in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        image_dir = self.image_dir.get()
        image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
        
        self.progress['maximum'] = len(image_files)
        success_count = 0
        
        self.output_text.insert(tk.END, f"Found {len(image_files)} images in {image_dir}\n")
        
        for i, image_file in enumerate(image_files):
            if not self.running:
                break
                
            image_path = os.path.join(image_dir, image_file)
            self.output_text.insert(tk.END, f"Processing {image_path}\n")
            self.root.update()
            
            self.analyze_image(image_path)
            success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
            
            self.progress['value'] = i + 1
            self.root.update()

        if self.running:
            # Save results
            output_file = f"geminiallimagestest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(self.results)
            df.to_excel(output_file, index=False)
            
            self.output_text.insert(tk.END, f"\nResults saved to {output_file}\n")
            self.output_text.insert(tk.END, f"Successfully processed {success_count} out of {len(image_files)} images\n")
        
        self.running = False
        self.process_btn.config(text="Process Images")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([prompt, img])
                result_text = response.text.strip()
                
                # Parse the response
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                self.results.append({
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.output_text.insert(tk.END, f"{result_text}\n\n")
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    self.output_text.insert(tk.END, f"429 error for {image_path}, retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        self.results.append({
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.output_text.insert(tk.END, f"Failed processing {image_path}: {error_msg}\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPAnalyzerApp(root)
    root.mainloop()
    

# single Image + folder
import google.generativeai as genai
from PIL import Image
import os
import pandas as pd
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt (same as original)
prompt = """
[Your original prompt remains unchanged here]
"""

class WWTPAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Image Analyzer")
        self.root.geometry("800x600")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # Directory selection frame
        dir_frame = tk.LabelFrame(self.root, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=50).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        # Single image selection frame
        img_frame = tk.LabelFrame(self.root, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=50).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        # Process button
        self.process_btn = tk.Button(self.root, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=10)

        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.root, width=90, height=20)
        self.output_text.pack(pady=10)

        # Status label
        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            self.output_text.insert(tk.END, f"Selected directory: {directory}\n")

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            self.output_text.insert(tk.END, f"Selected image: {image_file}\n")

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            self.output_text.insert(tk.END, "Please select either a directory or an image first!\n")
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        self.output_text.delete(1.0, tk.END)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        # Check if we're processing a single image or directory
        if self.single_image.get():
            self.progress['maximum'] = 1
            self.output_text.insert(tk.END, f"Processing single image: {self.single_image.get()}\n")
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            self.output_text.insert(tk.END, f"Found {len(image_files)} images in {image_dir}\n")
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                self.output_text.insert(tk.END, f"Processing {image_path}\n")
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            self.output_text.insert(tk.END, f"Successfully processed {success_count} out of {len(image_files)} images\n")

        if self.running:
            # Save results
            output_file = f"geminiallimagestest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(self.results)
            df.to_excel(output_file, index=False)
            self.output_text.insert(tk.END, f"\nResults saved to {output_file}\n")
        
        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([prompt, img])
                result_text = response.text.strip()
                
                # Parse the response
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                self.results.append({
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.output_text.insert(tk.END, f"{result_text}\n\n")
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    self.output_text.insert(tk.END, f"429 error for {image_path}, retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        self.results.append({
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.output_text.insert(tk.END, f"Failed processing {image_path}: {error_msg}\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPAnalyzerApp(root)
    root.mainloop()
    
    

#Outputs are not save to excel | image + folder
import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt (same as original)
prompt = """
[Your original prompt remains unchanged here]
"""

class WWTPAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Image Analyzer")
        self.root.geometry("800x600")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # Directory selection frame
        dir_frame = tk.LabelFrame(self.root, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=50).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        # Single image selection frame
        img_frame = tk.LabelFrame(self.root, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=50).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        # Process button
        self.process_btn = tk.Button(self.root, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(self.root, length=300, mode='determinate')
        self.progress.pack(pady=10)

        # Output text area
        self.output_text = scrolledtext.ScrolledText(self.root, width=90, height=20)
        self.output_text.pack(pady=10)

        # Status label
        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            self.output_text.insert(tk.END, f"Selected directory: {directory}\n")

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            self.output_text.insert(tk.END, f"Selected image: {image_file}\n")

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            self.output_text.insert(tk.END, "Please select either a directory or an image first!\n")
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        self.output_text.delete(1.0, tk.END)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        # Check if we're processing a single image or directory
        if self.single_image.get():
            self.progress['maximum'] = 1
            self.output_text.insert(tk.END, f"Processing single image: {self.single_image.get()}\n")
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            self.output_text.insert(tk.END, f"Found {len(image_files)} images in {image_dir}\n")
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                self.output_text.insert(tk.END, f"Processing {image_path}\n")
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            self.output_text.insert(tk.END, f"Successfully processed {success_count} out of {len(image_files)} images\n")

        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([prompt, img])
                result_text = response.text.strip()
                
                # Parse the response
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                self.results.append({
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.output_text.insert(tk.END, f"{result_text}\n\n")
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    self.output_text.insert(tk.END, f"429 error for {image_path}, retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        self.results.append({
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.output_text.insert(tk.END, f"Failed processing {image_path}: {error_msg}\n\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPAnalyzerApp(root)
    root.mainloop()    
    

#Chat bot included, partially correct
import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt for image analysis
image_prompt = """
[Your original prompt remains unchanged here]
"""

class WWTPChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Analysis Chatbot")
        self.root.geometry("900x700")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill="both", expand=True)

        # Left panel for controls
        control_frame = tk.Frame(main_frame)
        main_frame.add(control_frame, width=300)

        # Directory selection
        dir_frame = tk.LabelFrame(control_frame, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=30).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        # Single image selection
        img_frame = tk.LabelFrame(control_frame, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=30).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        # Process button
        self.process_btn = tk.Button(control_frame, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        # Progress bar
        self.progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.progress.pack(pady=10)

        # Right panel for chat
        chat_frame = tk.Frame(main_frame)
        main_frame.add(chat_frame)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(chat_frame, width=70, height=30)
        self.chat_display.pack(pady=10, padx=10)

        # Chat input frame
        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5, padx=10)
        
        self.chat_input = tk.Entry(input_frame, width=60)
        self.chat_input.pack(side=tk.LEFT, padx=5)
        self.chat_input.bind("<Return>", self.process_chat_input)
        
        tk.Button(input_frame, text="Send", command=self.process_chat_input).pack(side=tk.LEFT)

        # Status label
        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            self.chat_display.insert(tk.END, f"Bot: Selected directory: {directory}\n")

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            self.chat_display.insert(tk.END, f"Bot: Selected image: {image_file}\n")

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            self.chat_display.insert(tk.END, "Bot: Please select either a directory or an image first!\n")
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        if self.single_image.get():
            self.progress['maximum'] = 1
            self.chat_display.insert(tk.END, f"Bot: Processing single image: {self.single_image.get()}\n")
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            self.chat_display.insert(tk.END, f"Bot: Found {len(image_files)} images in {image_dir}\n")
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                self.chat_display.insert(tk.END, f"Bot: Processing {image_path}\n")
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            self.chat_display.insert(tk.END, f"Bot: Successfully processed {success_count} out of {len(image_files)} images\n")

        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([image_prompt, img])
                result_text = response.text.strip()
                
                # Parse the response
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                self.results.append({
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                self.chat_display.insert(tk.END, f"Bot: {result_text}\n\n")
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    self.chat_display.insert(tk.END, f"Bot: 429 error for {image_path}, retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        self.results.append({
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self.chat_display.insert(tk.END, f"Bot: Failed processing {image_path}: {error_msg}\n\n")

    def process_chat_input(self, event=None):
        user_input = self.chat_input.get().strip()
        if not user_input:
            return

        self.chat_display.insert(tk.END, f"You: {user_input}\n")
        self.chat_input.delete(0, tk.END)

        # Process the input in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.handle_chat_response, args=(user_input,))
        thread.start()

    def handle_chat_response(self, user_input):
        # Simple command processing
        if user_input.lower() in ["analyze", "start", "process"]:
            self.start_processing()
        elif user_input.lower() == "clear":
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, "Bot: Chat cleared\n")
        elif user_input.lower() == "status":
            self.chat_display.insert(tk.END, f"Bot: Current status: {'Running' if self.running else 'Idle'}\n")
        elif user_input.lower() == "help":
            self.chat_display.insert(tk.END, "Bot: Available commands:\n"
                                          "- analyze/start/process: Start image analysis\n"
                                          "- clear: Clear chat\n"
                                          "- status: Show current status\n"
                                          "- help: Show this message\n"
                                          "- Any other question: I'll try to answer!\n")
        else:
            # General question handling
            try:
                response = model.generate_content(user_input)
                self.chat_display.insert(tk.END, f"Bot: {response.text}\n")
            except Exception as e:
                self.chat_display.insert(tk.END, f"Bot: Sorry, I encountered an error: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPChatbotApp(root)
    root.mainloop()
    

import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt for image analysis
image_prompt = """
[Your original prompt remains unchanged here]
"""

class WWTPChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Analysis Chatbot")
        self.root.geometry("900x700")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False
        self.last_analyzed_image = None  # Store last analyzed image path
        self.last_analysis_result = None  # Store last analysis result

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill="both", expand=True)

        control_frame = tk.Frame(main_frame)
        main_frame.add(control_frame, width=300)

        dir_frame = tk.LabelFrame(control_frame, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=30).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        img_frame = tk.LabelFrame(control_frame, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=30).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        self.process_btn = tk.Button(control_frame, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        self.progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.progress.pack(pady=10)

        chat_frame = tk.Frame(main_frame)
        main_frame.add(chat_frame)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, width=70, height=30)
        self.chat_display.pack(pady=10, padx=10)

        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5, padx=10)
        
        self.chat_input = tk.Entry(input_frame, width=60)
        self.chat_input.pack(side=tk.LEFT, padx=5)
        self.chat_input.bind("<Return>", self.process_chat_input)
        
        tk.Button(input_frame, text="Send", command=self.process_chat_input).pack(side=tk.LEFT)

        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            self.chat_display.insert(tk.END, f"Bot: Selected directory: {directory}\n")

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            self.chat_display.insert(tk.END, f"Bot: Selected image: {image_file}\n")

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            self.chat_display.insert(tk.END, "Bot: Please select either a directory or an image first!\n")
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        if self.single_image.get():
            self.progress['maximum'] = 1
            self.chat_display.insert(tk.END, f"Bot: Processing single image: {self.single_image.get()}\n")
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            self.chat_display.insert(tk.END, f"Bot: Found {len(image_files)} images in {image_dir}\n")
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                self.chat_display.insert(tk.END, f"Bot: Processing {image_path}\n")
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            self.chat_display.insert(tk.END, f"Bot: Successfully processed {success_count} out of {len(image_files)} images\n")

        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([image_prompt, img])
                result_text = response.text.strip()
                
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                result_dict = {
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.results.append(result_dict)
                self.last_analyzed_image = image_path
                self.last_analysis_result = result_text
                self.chat_display.insert(tk.END, f"Bot: {result_text}\n\n")
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    self.chat_display.insert(tk.END, f"Bot: 429 error for {image_path}, retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        result_dict = {
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result_dict)
        self.last_analyzed_image = image_path
        self.last_analysis_result = f"Failed processing {image_path}: {error_msg}"
        self.chat_display.insert(tk.END, f"Bot: Failed processing {image_path}: {error_msg}\n\n")

    def process_chat_input(self, event=None):
        user_input = self.chat_input.get().strip()
        if not user_input:
            return

        self.chat_display.insert(tk.END, f"You: {user_input}\n")
        self.chat_input.delete(0, tk.END)

        thread = threading.Thread(target=self.handle_chat_response, args=(user_input,))
        thread.start()

    def handle_chat_response(self, user_input):
        # Command processing
        if user_input.lower() in ["analyze", "start", "process"]:
            self.start_processing()
        elif user_input.lower() == "clear":
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, "Bot: Chat cleared\n")
        elif user_input.lower() == "status":
            self.chat_display.insert(tk.END, f"Bot: Current status: {'Running' if self.running else 'Idle'}\n")
        elif user_input.lower() == "help":
            self.chat_display.insert(tk.END, "Bot: Available commands:\n"
                                          "- analyze/start/process: Start image analysis\n"
                                          "- clear: Clear chat\n"
                                          "- status: Show current status\n"
                                          "- help: Show this message\n"
                                          "- Questions about last image: Ask about the previously analyzed image\n"
                                          "- Any other question: I'll try to answer!\n")
        else:
            # Check if the question might be about the last analyzed image
            image_keywords = ["image", "picture", "photo", "this", "it", "area", "location", "place"]
            if self.last_analyzed_image and any(keyword in user_input.lower() for keyword in image_keywords):
                try:
                    # Use the last analysis result as context
                    context = f"Based on this analysis of {self.last_analyzed_image}:\n{self.last_analysis_result}\n\nQuestion: {user_input}"
                    response = model.generate_content(context)
                    self.chat_display.insert(tk.END, f"Bot: {response.text}\n")
                except Exception as e:
                    self.chat_display.insert(tk.END, f"Bot: Sorry, I encountered an error: {str(e)}\n")
            else:
                # General question handling
                try:
                    response = model.generate_content(user_input)
                    self.chat_display.insert(tk.END, f"Bot: {response.text}\n")
                except Exception as e:
                    self.chat_display.insert(tk.END, f"Bot: Sorry, I encountered an error: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPChatbotApp(root)
    root.mainloop()    
    


import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt for image analysis
image_prompt = """
[Your original prompt remains unchanged here]
"""

class WWTPChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Analysis Chatbot")
        self.root.geometry("900x700")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False
        self.last_analyzed_image = None  # Store last analyzed image path
        self.last_analysis_result = None  # Store last analysis result

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill="both", expand=True)

        control_frame = tk.Frame(main_frame)
        main_frame.add(control_frame, width=300)

        dir_frame = tk.LabelFrame(control_frame, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=30).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        img_frame = tk.LabelFrame(control_frame, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=30).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        self.process_btn = tk.Button(control_frame, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        self.progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.progress.pack(pady=10)

        chat_frame = tk.Frame(main_frame)
        main_frame.add(chat_frame)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, width=70, height=30)
        self.chat_display.pack(pady=10, padx=10)

        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5, padx=10)
        
        self.chat_input = tk.Entry(input_frame, width=60)
        self.chat_input.pack(side=tk.LEFT, padx=5)
        self.chat_input.bind("<Return>", self.process_chat_input)
        
        tk.Button(input_frame, text="Send", command=self.process_chat_input).pack(side=tk.LEFT)

        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            self.chat_display.insert(tk.END, f"Bot: Selected directory: {directory}\n")

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            self.chat_display.insert(tk.END, f"Bot: Selected image: {image_file}\n")

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            self.chat_display.insert(tk.END, "Bot: Please select either a directory or an image first!\n")
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        if self.single_image.get():
            self.progress['maximum'] = 1
            self.chat_display.insert(tk.END, f"Bot: Processing single image: {self.single_image.get()}\n")
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            self.chat_display.insert(tk.END, f"Bot: Found {len(image_files)} images in {image_dir}\n")
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                self.chat_display.insert(tk.END, f"Bot: Processing {image_path}\n")
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            self.chat_display.insert(tk.END, f"Bot: Successfully processed {success_count} out of {len(image_files)} images\n")

        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([image_prompt, img])
                result_text = response.text.strip()
                
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                result_dict = {
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self.results.append(result_dict)
                self.last_analyzed_image = image_path
                self.last_analysis_result = result_text
                self.chat_display.insert(tk.END, f"Bot: {result_text}\n\n")
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    self.chat_display.insert(tk.END, f"Bot: 429 error for {image_path}, retrying in 10 seconds...\n")
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        result_dict = {
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results.append(result_dict)
        self.last_analyzed_image = image_path
        self.last_analysis_result = f"Failed processing {image_path}: {error_msg}"
        self.chat_display.insert(tk.END, f"Bot: Failed processing {image_path}: {error_msg}\n\n")

    def process_chat_input(self, event=None):
        user_input = self.chat_input.get().strip()
        if not user_input:
            return

        self.chat_display.insert(tk.END, f"You: {user_input}\n")
        self.chat_input.delete(0, tk.END)

        thread = threading.Thread(target=self.handle_chat_response, args=(user_input,))
        thread.start()

    def handle_chat_response(self, user_input):
        # Command processing
        if user_input.lower() in ["analyze", "start", "process"]:
            self.start_processing()
        elif user_input.lower() == "clear":
            self.chat_display.delete(1.0, tk.END)
            self.chat_display.insert(tk.END, "Bot: Chat cleared\n")
        elif user_input.lower() == "status":
            self.chat_display.insert(tk.END, f"Bot: Current status: {'Running' if self.running else 'Idle'}\n")
        elif user_input.lower() == "help":
            self.chat_display.insert(tk.END, "Bot: Available commands:\n"
                                          "- analyze/start/process: Start image analysis\n"
                                          "- clear: Clear chat\n"
                                          "- status: Show current status\n"
                                          "- help: Show this message\n"
                                          "- Questions about last image: Ask about the previously analyzed image\n"
                                          "- Any other question: I'll try to answer!\n")
        else:
            # Check if the question might be about the last analyzed image
            image_keywords = ["image", "picture", "photo", "this", "it", "area", "location", "place"]
            if self.last_analyzed_image and any(keyword in user_input.lower() for keyword in image_keywords):
                try:
                    # Use the last analysis result as context
                    context = f"Based on this analysis of {self.last_analyzed_image}:\n{self.last_analysis_result}\n\nQuestion: {user_input}"
                    response = model.generate_content(context)
                    self.chat_display.insert(tk.END, f"Bot: {response.text}\n")
                except Exception as e:
                    self.chat_display.insert(tk.END, f"Bot: Sorry, I encountered an error: {str(e)}\n")
            else:
                # General question handling
                try:
                    response = model.generate_content(user_input)
                    self.chat_display.insert(tk.END, f"Bot: {response.text}\n")
                except Exception as e:
                    self.chat_display.insert(tk.END, f"Bot: Sorry, I encountered an error: {str(e)}\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPChatbotApp(root)
    root.mainloop()



import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt for image analysis
image_prompt = """
Analyze the provided image to determine if it depicts a wastewater treatment plant (WWTP). A WWTP is a system of interconnected units, not just isolated tanks. Use the following detailed guidelines to identify WWTP components and their arrangement, as their presence and logical layout are key to a positive identification:

*IDENTIFY WASTEWATER TREATMENT PLANT (WWTP) COMPONENTS:*

1.A. TANKS (Detailed Identification Rules):
   - Circular Tanks: Round structures made of concrete, steel, or other materials. Sizes vary greatly. Some may have covers or domes (appearing as solid circles), and some may have central mechanisms (e.g., rotating scraper arms). Count those with water (dark color) and without water (light color) separately.
   - Rectangular Tanks: Elongated basins, often with a length-to-width ratio of 3:1 to 5:1. They may appear singly, in groups, or in parallel series, sometimes with internal dividers or walls. Corners may not always be sharp. Count those with water (dark color) and without water (light color) separately.
   - Primary Sedimentation Tanks (PSTs): Predominantly circular and among the larger circular tanks. Look for a central mechanism (rotating scraper arm) and a darker central sludge hopper. Rectangular PSTs are less common but may have a longitudinal collector mechanism.

1.B. OTHER KEY WWTP INFRASTRUCTURE (Beyond Tanks):
   - Aeration Basins: Typically large rectangular basins, though circular or oval shapes are possible. Look for surface agitation (ripples, waves), visible aerators, or bubble patterns. Water may appear brownish due to microbial activity.
   - Clarifiers (Secondary Settling Tanks): Can be circular or rectangular, often downstream of aeration basins. Water may appear clearer than in PSTs. Circular clarifiers may have central mechanisms, potentially smaller than those in PSTs.
   - Sludge Drying Beds: Rectangular areas with clear divisions or rows. Look for drying sludge texture, changing from dark brown (wet) to lighter shades (dry). Often near settling tanks or clarifiers.
   - Inlet and Outlet Structures: Look for pipes, channels, or canals entering (from populated/industrial areas) and exiting (to a river, lake, or ocean). Pumping stations (small buildings) may be nearby.
   - Digesters: Tall, cylindrical tanks with conical bottoms or dome-shaped tops, often near sludge handling areas. A strong indicator if present.
   - Buildings: Administrative, laboratory, or equipment buildings. Support identification but are not definitive alone.

1.C. OVERALL LAYOUT AND INTERCONNECTEDNESS:
   - A functioning WWTP has a logical flow, e.g., Inlet -> PSTs -> Aeration Basins -> Clarifiers -> Outlet. Sludge handling (drying beds, digesters) is typically near PSTs and clarifiers. This spatial coherence strongly supports identification.

*INSTRUCTIONS:*
- If the image depicts a WWTP, provide a brief description of the scene and count the following:
  - Number of circular features (e.g., tanks, clarifiers).
  - Number of rectangular features (e.g., buildings, basins).
  - Number of circular features with water (dark color).
  - Number of circular features without water (light color).
  - Number of rectangular features with water (dark color).
  - Number of rectangular features without water (light color).
- If it is not a WWTP, provide a brief description and set all counts to 0.
- Use the provided guidelines to ensure accurate identification and differentiation of features.
- For all counts, provide only an integer value (e.g., 5, 10, 0). If exact counting is difficult due to resolution or overlapping features, estimate the number as an integer without additional text or qualifiers (e.g., use 20 instead of '20+' or '20 (approximate)').

*RESPONSE FORMAT:*
- Is it a WWTP? [Yes/No]
- Description: [Brief description]
- Circular Features: [Number]
- Rectangular Features: [Number]
- Circular Features with Water: [Number]
- Circular Features without Water: [Number]
- Rectangular Features with Water: [Number]
- Rectangular Features without Water: [Number]
"""

class WWTPChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Analysis Chatbot")
        self.root.geometry("900x700")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False
        self.last_analyzed_image = None
        self.last_analysis_result = None
        self.chat_history = []

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill="both", expand=True)

        control_frame = tk.Frame(main_frame)
        main_frame.add(control_frame, width=300)

        dir_frame = tk.LabelFrame(control_frame, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=30).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        img_frame = tk.LabelFrame(control_frame, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=30).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        self.process_btn = tk.Button(control_frame, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        self.progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.progress.pack(pady=10)

        chat_frame = tk.Frame(main_frame)
        main_frame.add(chat_frame)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, width=70, height=30)
        self.chat_display.pack(pady=10, padx=10)

        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5, padx=10)
        
        self.chat_input = tk.Entry(input_frame, width=60)
        self.chat_input.pack(side=tk.LEFT, padx=5)
        self.chat_input.bind("<Return>", self.process_chat_input)
        
        tk.Button(input_frame, text="Send", command=self.process_chat_input).pack(side=tk.LEFT)

        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            message = f"Bot: Selected directory: {directory}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            message = f"Bot: Selected image: {image_file}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            message = "Bot: Please select either a directory or an image first!\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        if self.single_image.get():
            self.progress['maximum'] = 1
            message = f"Bot: Processing single image: {self.single_image.get()}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            message = f"Bot: Found {len(image_files)} images in {image_dir}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                message = f"Bot: Processing {image_path}\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", message.strip()))
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            message = f"Bot: Successfully processed {success_count} out of {len(image_files)} images\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([image_prompt, img])
                result_text = response.text.strip()
                
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                result_dict = {
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Raw Text": result_text
                }
                self.results.append(result_dict)
                self.last_analyzed_image = image_path
                self.last_analysis_result = result_dict
                
                message = f"Bot: Analysis of {image_name}:\n" \
                         f"Is it a WWTP? {is_wwtp}\n" \
                         f"Number of Circular Features: {circular_count}\n" \
                         f"Number of Rectangular Features: {rectangular_count}\n" \
                         f"Description: {description}\n\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", result_text))
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    message = f"Bot: 429 error for {image_path}, retrying in 10 seconds...\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        result_dict = {
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Raw Text": f"Failed processing {image_path}: {error_msg}"
        }
        self.results.append(result_dict)
        self.last_analyzed_image = image_path
        self.last_analysis_result = result_dict
        
        message = f"Bot: Analysis of {image_name}:\n" \
                 f"Is it a WWTP? N/A\n" \
                 f"Number of Circular Features: 0\n" \
                 f"Number of Rectangular Features: 0\n" \
                 f"Description: Error: {error_msg}\n\n"
        self.chat_display.insert(tk.END, message)
        self.chat_history.append(("Bot", result_dict["Raw Text"]))

    def process_chat_input(self, event=None):
        user_input = self.chat_input.get().strip()
        if not user_input:
            return

        self.chat_display.insert(tk.END, f"You: {user_input}\n")
        self.chat_history.append(("You", user_input))
        self.chat_input.delete(0, tk.END)

        thread = threading.Thread(target=self.handle_chat_response, args=(user_input,))
        thread.start()

    def retrieve_relevant_history(self, user_input):
        keywords = user_input.lower().split()
        relevant_history = []
        
        for sender, message in reversed(self.chat_history[-20:]):
            if any(keyword in message.lower() for keyword in keywords):
                relevant_history.append(f"{sender}: {message}")
        
        return "\n".join(reversed(relevant_history)) if relevant_history else "No relevant history found."

    def handle_chat_response(self, user_input):
        if user_input.lower() in ["analyze", "start", "process"]:
            self.start_processing()
        elif user_input.lower() == "clear":
            self.chat_display.delete(1.0, tk.END)
            self.chat_history.clear()
            message = "Bot: Chat cleared\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
        elif user_input.lower() == "status":
            message = f"Bot: Current status: {'Running' if self.running else 'Idle'}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
        elif user_input.lower() == "history":
            history = "\n".join(f"{sender}: {msg}" for sender, msg in self.chat_history[-10:])
            message = f"Bot: Recent chat history:\n{history}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
        elif user_input.lower() == "help":
            message = "Bot: Available commands:\n" \
                     "- analyze/start/process: Start image analysis\n" \
                     "- clear: Clear chat\n" \
                     "- status: Show current status\n" \
                     "- history: Show recent chat history\n" \
                     "- help: Show this message\n" \
                     "- Questions about last image: Ask about counts, features, or description\n" \
                     "- Any other question: I'll try to answer with chat history context!\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
        else:
            if self.last_analyzed_image and self.last_analysis_result:
                lower_input = user_input.lower()
                if "circular" in lower_input and ("how many" in lower_input or "count" in lower_input or "number" in lower_input):
                    count = self.last_analysis_result["Num of Circular Features"]
                    message = f"Bot: The last analyzed image ({self.last_analysis_result['Image Name']}) has {count} circular features.\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
                elif "rectangular" in lower_input and ("how many" in lower_input or "count" in lower_input or "number" in lower_input):
                    count = self.last_analysis_result["Num of Rectangular Features"]
                    message = f"Bot: The last analyzed image ({self.last_analysis_result['Image Name']}) has {count} rectangular features.\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
                else:
                    try:
                        relevant_history = self.retrieve_relevant_history(user_input)
                        context = f"Chat History:\n{relevant_history}\n\n" \
                                f"Last Image Analysis ({self.last_analyzed_image}):\n" \
                                f"Is it a WWTP? {self.last_analysis_result['Is WWTP?']}\n" \
                                f"Number of Circular Features: {self.last_analysis_result['Num of Circular Features']}\n" \
                                f"Number of Rectangular Features: {self.last_analysis_result['Num of Rectangular Features']}\n" \
                                f"Description: {self.last_analysis_result['Description']}\n\n" \
                                f"Question: {user_input}"
                        response = model.generate_content(context)
                        message = f"Bot: {response.text}\n"
                        self.chat_display.insert(tk.END, message)
                        self.chat_history.append(("Bot", message.strip()))
                    except Exception as e:
                        message = f"Bot: Sorry, I encountered an error: {str(e)}\n"
                        self.chat_display.insert(tk.END, message)
                        self.chat_history.append(("Bot", message.strip()))
            else:
                try:
                    relevant_history = self.retrieve_relevant_history(user_input)
                    context = f"Chat History:\n{relevant_history}\n\nQuestion: {user_input}"
                    response = model.generate_content(context)
                    message = f"Bot: {response.text}\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
                except Exception as e:
                    message = f"Bot: Sorry, I encountered an error: {str(e)}\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPChatbotApp(root)
    root.mainloop()
    

import google.generativeai as genai
from PIL import Image
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt for initial WWTP analysis
image_prompt = """
Analyze the provided image to determine if it depicts a wastewater treatment plant (WWTP). A WWTP is a system of interconnected units, not just isolated tanks. Use the following detailed guidelines to identify WWTP components and their arrangement, as their presence and logical layout are key to a positive identification:

*IDENTIFY WASTEWATER TREATMENT PLANT (WWTP) COMPONENTS:*

1.A. TANKS (Detailed Identification Rules):
   - Circular Tanks: Round structures made of concrete, steel, or other materials. Sizes vary greatly. Some may have covers or domes (appearing as solid circles), and some may have central mechanisms (e.g., rotating scraper arms). Count those with water (dark color) and without water (light color) separately.
   - Rectangular Tanks: Elongated basins, often with a length-to-width ratio of 3:1 to 5:1. They may appear singly, in groups, or in parallel series, sometimes with internal dividers or walls. Corners may not always be sharp. Count those with water (dark color) and without water (light color) separately.
   - Primary Sedimentation Tanks (PSTs): Predominantly circular and among the larger circular tanks. Look for a central mechanism (rotating scraper arm) and a darker central sludge hopper. Rectangular PSTs are less common but may have a longitudinal collector mechanism.

1.B. OTHER KEY WWTP INFRASTRUCTURE (Beyond Tanks):
   - Aeration Basins: Typically large rectangular basins, though circular or oval shapes are possible. Look for surface agitation (ripples, waves), visible aerators, or bubble patterns. Water may appear brownish due to microbial activity.
   - Clarifiers (Secondary Settling Tanks): Can be circular or rectangular, often downstream of aeration basins. Water may appear clearer than in PSTs. Circular clarifiers may have central mechanisms, potentially smaller than those in PSTs.
   - Sludge Drying Beds: Rectangular areas with clear divisions or rows. Look for drying sludge texture, changing from dark brown (wet) to lighter shades (dry). Often near settling tanks or clarifiers.
   - Inlet and Outlet Structures: Look for pipes, channels, or canals entering (from populated/industrial areas) and exiting (to a river, lake, or ocean). Pumping stations (small buildings) may be nearby.
   - Digesters: Tall, cylindrical tanks with conical bottoms or dome-shaped tops, often near sludge handling areas. A strong indicator if present.
   - Buildings: Administrative, laboratory, or equipment buildings. Support identification but are not definitive alone.

1.C. OVERALL LAYOUT AND INTERCONNECTEDNESS:
   - A functioning WWTP has a logical flow, e.g., Inlet -> PSTs -> Aeration Basins -> Clarifiers -> Outlet. Sludge handling (drying beds, digesters) is typically near PSTs and clarifiers. This spatial coherence strongly supports identification.

*INSTRUCTIONS:*
- If the image depicts a WWTP, provide a brief description of the scene and count the following:
  - Number of circular features (e.g., tanks, clarifiers).
  - Number of rectangular features (e.g., buildings, basins).
  - Number of circular features with water (dark color).
  - Number of circular features without water (light color).
  - Number of rectangular features with water (dark color).
  - Number of rectangular features without water (light color).
- If it is not a WWTP, provide a brief description and set all counts to 0.
- Use the provided guidelines to ensure accurate identification and differentiation of features.
- For all counts, provide only an integer value (e.g., 5, 10, 0). If exact counting is difficult due to resolution or overlapping features, estimate the number as an integer without additional text or qualifiers (e.g., use 20 instead of '20+' or '20 (approximate)').

*RESPONSE FORMAT:*
- Is it a WWTP? [Yes/No]
- Description: [Brief description]
- Circular Features: [Number]
- Rectangular Features: [Number]
- Circular Features with Water: [Number]
- Circular Features without Water: [Number]
- Rectangular Features with Water: [Number]
- Rectangular Features without Water: [Number]
"""

class WWTPChatbotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WWTP Analysis Chatbot")
        self.root.geometry("900x700")

        # Variables
        self.image_dir = tk.StringVar()
        self.single_image = tk.StringVar()
        self.results = []
        self.running = False
        self.last_analyzed_image_path = None
        self.last_analyzed_image = None
        self.last_analysis_result = None
        self.chat_history = []

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill="both", expand=True)

        control_frame = tk.Frame(main_frame)
        main_frame.add(control_frame, width=300)

        dir_frame = tk.LabelFrame(control_frame, text="Analyze Directory", padx=10, pady=10)
        dir_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(dir_frame, text="Image Directory:").pack()
        tk.Entry(dir_frame, textvariable=self.image_dir, width=30).pack(pady=5)
        tk.Button(dir_frame, text="Browse Directory", command=self.browse_directory).pack(pady=5)

        img_frame = tk.LabelFrame(control_frame, text="Analyze Single Image", padx=10, pady=10)
        img_frame.pack(pady=5, padx=5, fill="x")
        tk.Label(img_frame, text="Single Image:").pack()
        tk.Entry(img_frame, textvariable=self.single_image, width=30).pack(pady=5)
        tk.Button(img_frame, text="Browse Image", command=self.browse_image).pack(pady=5)

        self.process_btn = tk.Button(control_frame, text="Analyze", command=self.start_processing)
        self.process_btn.pack(pady=10)

        self.progress = ttk.Progressbar(control_frame, length=200, mode='determinate')
        self.progress.pack(pady=10)

        chat_frame = tk.Frame(main_frame)
        main_frame.add(chat_frame)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, width=70, height=30)
        self.chat_display.pack(pady=10, padx=10)

        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5, padx=10)
        
        self.chat_input = tk.Entry(input_frame, width=60)
        self.chat_input.pack(side=tk.LEFT, padx=5)
        self.chat_input.bind("<Return>", self.process_chat_input)
        
        tk.Button(input_frame, text="Send", command=self.process_chat_input).pack(side=tk.LEFT)

        self.status = tk.Label(self.root, text="")
        self.status.pack(pady=5)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.image_dir.set(directory)
            message = f"Bot: Selected directory: {directory}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

    def browse_image(self):
        image_file = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg *.tif *.tiff")]
        )
        if image_file:
            self.single_image.set(image_file)
            message = f"Bot: Selected image: {image_file}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

    def start_processing(self):
        if not self.image_dir.get() and not self.single_image.get():
            message = "Bot: Please select either a directory or an image first!\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            return
        
        if self.running:
            self.running = False
            self.process_btn.config(text="Analyze")
            return

        self.running = True
        self.process_btn.config(text="Stop")
        self.results.clear()
        
        thread = threading.Thread(target=self.process_images)
        thread.start()

    def process_images(self):
        if self.single_image.get():
            self.progress['maximum'] = 1
            message = f"Bot: Processing single image: {self.single_image.get()}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            self.analyze_image(self.single_image.get())
            self.progress['value'] = 1
        elif self.image_dir.get():
            image_dir = self.image_dir.get()
            image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.tif', '.tiff'))]
            
            self.progress['maximum'] = len(image_files)
            success_count = 0
            
            message = f"Bot: Found {len(image_files)} images in {image_dir}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            
            for i, image_file in enumerate(image_files):
                if not self.running:
                    break
                    
                image_path = os.path.join(image_dir, image_file)
                message = f"Bot: Processing {image_path}\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", message.strip()))
                self.root.update()
                
                self.analyze_image(image_path)
                success_count += 1 if self.results[-1]["Is WWTP?"] != "N/A" else 0
                
                self.progress['value'] = i + 1
                self.root.update()
            
            message = f"Bot: Successfully processed {success_count} out of {len(image_files)} images\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

        self.running = False
        self.process_btn.config(text="Analyze")
        self.status.config(text="Processing Complete" if self.running else "Processing Stopped")

    def analyze_image(self, image_path, max_retries=3, rate_limit_delay=4):
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                response = model.generate_content([image_prompt, img])
                result_text = response.text.strip()
                
                lines = result_text.split('\n')
                is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
                description = "N/A"
                circular_count = 0
                rectangular_count = 0
                circular_with_water = 0
                circular_without_water = 0
                rectangular_with_water = 0
                rectangular_without_water = 0
                
                def extract_number(text):
                    match = re.search(r'\d+', text)
                    return int(match.group()) if match else 0

                for line in lines:
                    if "Description:" in line:
                        description = line.split('Description:')[1].strip()
                    elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                        circular_count = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                        rectangular_count = extract_number(line.split(':')[1].strip())
                    elif "Circular Features with Water:" in line:
                        circular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Circular Features without Water:" in line:
                        circular_without_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features with Water:" in line:
                        rectangular_with_water = extract_number(line.split(':')[1].strip())
                    elif "Rectangular Features without Water:" in line:
                        rectangular_without_water = extract_number(line.split(':')[1].strip())
                
                image_name = os.path.basename(image_path)
                result_dict = {
                    "Image Name": image_name,
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Raw Text": result_text
                }
                self.results.append(result_dict)
                self.last_analyzed_image_path = image_path
                self.last_analyzed_image = img
                self.last_analysis_result = result_dict
                
                message = f"Bot: Analysis of {image_name}:\n" \
                         f"Is it a WWTP? {is_wwtp}\n" \
                         f"Number of Circular Features: {circular_count}\n" \
                         f"Number of Rectangular Features: {rectangular_count}\n" \
                         f"Description: {description}\n\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", result_text))
                break
            except exceptions.ResourceExhausted as e:
                if attempt < max_retries - 1:
                    message = f"Bot: 429 error for {image_path}, retrying in 10 seconds...\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
                    time.sleep(10)
                else:
                    self.handle_error(image_path, str(e))
            except Exception as e:
                if attempt == max_retries - 1:
                    self.handle_error(image_path, str(e))
                time.sleep(2)
        time.sleep(rate_limit_delay)

    def handle_error(self, image_path, error_msg):
        image_name = os.path.basename(image_path)
        result_dict = {
            "Image Name": image_name,
            "Is WWTP?": "N/A",
            "Num of Circular Features": 0,
            "Num of Rectangular Features": 0,
            "Num of Circular Features with Water": 0,
            "Num of Circular Features without Water": 0,
            "Num of Rectangular Features with Water": 0,
            "Num of Rectangular Features without Water": 0,
            "Description": f"Error: {error_msg}",
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Raw Text": f"Failed processing {image_path}: {error_msg}"
        }
        self.results.append(result_dict)
        self.last_analyzed_image_path = image_path
        self.last_analyzed_image = None
        self.last_analysis_result = result_dict
        
        message = f"Bot: Analysis of {image_name}:\n" \
                 f"Is it a WWTP? N/A\n" \
                 f"Number of Circular Features: 0\n" \
                 f"Number of Rectangular Features: 0\n" \
                 f"Description: Error: {error_msg}\n\n"
        self.chat_display.insert(tk.END, message)
        self.chat_history.append(("Bot", result_dict["Raw Text"]))

    def process_chat_input(self, event=None):
        user_input = self.chat_input.get().strip()
        if not user_input:
            return

        self.chat_display.insert(tk.END, f"You: {user_input}\n")
        self.chat_history.append(("You", user_input))
        self.chat_input.delete(0, tk.END)

        thread = threading.Thread(target=self.handle_chat_response, args=(user_input,))
        thread.start()

    def retrieve_relevant_history(self, user_input):
        keywords = user_input.lower().split()
        relevant_history = []
        
        for sender, message in reversed(self.chat_history[-20:]):
            if any(keyword in message.lower() for keyword in keywords):
                relevant_history.append(f"{sender}: {message}")
        
        return "\n".join(reversed(relevant_history)) if relevant_history else "No relevant history found."

    def handle_chat_response(self, user_input):
        lower_input = user_input.lower()
        
        # Handle commands first
        if lower_input in ["analyze", "start", "process"]:
            self.start_processing()
            return
        elif lower_input == "clear":
            self.chat_display.delete(1.0, tk.END)
            self.chat_history.clear()
            message = "Bot: Chat cleared\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            return
        elif lower_input == "status":
            message = f"Bot: Current status: {'Running' if self.running else 'Idle'}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            return
        elif lower_input == "history":
            history = "\n".join(f"{sender}: {msg}" for sender, msg in self.chat_history[-10:])
            message = f"Bot: Recent chat history:\n{history}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            return
        elif lower_input == "help":
            message = "Bot: Available commands:\n" \
                     "- analyze/start/process: Start image analysis\n" \
                     "- clear: Clear chat\n" \
                     "- status: Show current status\n" \
                     "- history: Show recent chat history\n" \
                     "- help: Show this message\n" \
                     "- Questions about last image: Ask anything about the image content (e.g., features, objects, details)\n" \
                     "- General questions: I'll answer using chat history context\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
            return

        # Handle image-related questions if an image exists
        if self.last_analyzed_image_path and self.last_analysis_result:
            # Specific feature counts from initial analysis
            if "circular" in lower_input and ("how many" in lower_input or "count" in lower_input or "number" in lower_input):
                count = self.last_analysis_result["Num of Circular Features"]
                message = f"Bot: The last analyzed image ({self.last_analysis_result['Image Name']}) has {count} circular features.\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", message.strip()))
                return

            if "rectangular" in lower_input and ("how many" in lower_input or "count" in lower_input or "number" in lower_input):
                count = self.last_analysis_result["Num of Rectangular Features"]
                message = f"Bot: The last analyzed image ({self.last_analysis_result['Image Name']}) has {count} rectangular features.\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", message.strip()))
                return

            # Any other question about the image triggers re-analysis
            if self.last_analyzed_image:
                try:
                    # Re-analyze the image with the user's exact question
                    custom_prompt = f"Analyze the image and answer the following question: {user_input}\nProvide a clear answer (yes/no if applicable) and a brief explanation.\n\nImage: {self.last_analyzed_image_path}"
                    response = model.generate_content([custom_prompt, self.last_analyzed_image])
                    message = f"Bot: {response.text}\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
                except Exception as e:
                    message = f"Bot: Sorry, I encountered an error while re-analyzing the image: {str(e)}\n"
                    self.chat_display.insert(tk.END, message)
                    self.chat_history.append(("Bot", message.strip()))
            else:
                message = "Bot: No image available to analyze. Please analyze an image first.\n"
                self.chat_display.insert(tk.END, message)
                self.chat_history.append(("Bot", message.strip()))
            return

        # Handle general questions if no image is available or question isn't image-related
        try:
            relevant_history = self.retrieve_relevant_history(user_input)
            context = f"Chat History:\n{relevant_history}\n\nQuestion: {user_input}"
            response = model.generate_content(context)
            message = f"Bot: {response.text}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))
        except Exception as e:
            message = f"Bot: Sorry, I encountered an error: {str(e)}\n"
            self.chat_display.insert(tk.END, message)
            self.chat_history.append(("Bot", message.strip()))

if __name__ == "__main__":
    root = tk.Tk()
    app = WWTPChatbotApp(root)
    root.mainloop()
    
'''

#Streamlit
import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os
from datetime import datetime
import time
from google.api_core import exceptions
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API keys
API_KEYS = [
    "AIzaSyCjDmZD-dCcRuCfjIKLwufOTgHxaCFZgdo",
    "AIzaSyCe-JWBbgReQulpm7TYh8_fqi-37vwvLu8"
]
API_KEY = API_KEYS[0]
genai.configure(api_key=API_KEY)

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Prompt for initial WWTP analysis
image_prompt = """
Analyze the provided image to determine if it depicts a wastewater treatment plant (WWTP). A WWTP is a system of interconnected units, not just isolated tanks. Use the following detailed guidelines to identify WWTP components and their arrangement, as their presence and logical layout are key to a positive identification:

*IDENTIFY WASTEWATER TREATMENT PLANT (WWTP) COMPONENTS:*

1.A. TANKS (Detailed Identification Rules):
   - Circular Tanks: Round structures made of concrete, steel, or other materials. Sizes vary greatly. Some may have covers or domes (appearing as solid circles), and some may have central mechanisms (e.g., rotating scraper arms). Count those with water (dark color) and without water (light color) separately.
   - Rectangular Tanks: Elongated basins, often with a length-to-width ratio of 3:1 to 5:1. They may appear singly, in groups, or in parallel series, sometimes with internal dividers or walls. Corners may not always be sharp. Count those with water (dark color) and without water (light color) separately.
   - Primary Sedimentation Tanks (PSTs): Predominantly circular and among the larger circular tanks. Look for a central mechanism (rotating scraper arm) and a darker central sludge hopper. Rectangular PSTs are less common but may have a longitudinal collector mechanism.

1.B. OTHER KEY WWTP INFRASTRUCTURE (Beyond Tanks):
   - Aeration Basins: Typically large rectangular basins, though circular or oval shapes are possible. Look for surface agitation (ripples, waves), visible aerators, or bubble patterns. Water may appear brownish due to microbial activity.
   - Clarifiers (Secondary Settling Tanks): Can be circular or rectangular, often downstream of aeration basins. Water may appear clearer than in PSTs. Circular clarifiers may have central mechanisms, potentially smaller than those in PSTs.
   - Sludge Drying Beds: Rectangular areas with clear divisions or rows. Look for drying sludge texture, changing from dark brown (wet) to lighter shades (dry). Often near settling tanks or clarifiers.
   - Inlet and Outlet Structures: Look for pipes, channels, or canals entering (from populated/industrial areas) and exiting (to a river, lake, or ocean). Pumping stations (small buildings) may be nearby.
   - Digesters: Tall, cylindrical tanks with conical bottoms or dome-shaped tops, often near sludge handling areas. A strong indicator if present.
   - Buildings: Administrative, laboratory, or equipment buildings. Support identification but are not definitive alone.

1.C. OVERALL LAYOUT AND INTERCONNECTEDNESS:
   - A functioning WWTP has a logical flow, e.g., Inlet -> PSTs -> Aeration Basins -> Clarifiers -> Outlet. Sludge handling (drying beds, digesters) is typically near PSTs and clarifiers. This spatial coherence strongly supports identification.

*INSTRUCTIONS:*
- If the image depicts a WWTP, provide a brief description of the scene and count the following:
  - Number of circular features (e.g., tanks, clarifiers).
  - Number of rectangular features (e.g., buildings, basins).
  - Number of circular features with water (dark color).
  - Number of circular features without water (light color).
  - Number of rectangular features with water (dark color).
  - Number of rectangular features without water (light color).
- If it is not a WWTP, provide a brief description and set all counts to 0.
- Use the provided guidelines to ensure accurate identification and differentiation of features.
- For all counts, provide only an integer value (e.g., 5, 10, 0). If exact counting is difficult due to resolution or overlapping features, estimate the number as an integer without additional text or qualifiers (e.g., use 20 instead of '20+' or '20 (approximate)').

*RESPONSE FORMAT:*
- Is it a WWTP? [Yes/No]
- Description: [Brief description]
- Circular Features: [Number]
- Rectangular Features: [Number]
- Circular Features with Water: [Number]
- Circular Features without Water: [Number]
- Rectangular Features with Water: [Number]
- Rectangular Features without Water: [Number]
"""

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_analyzed_image' not in st.session_state:
    st.session_state.last_analyzed_image = None
if 'last_analyzed_image_path' not in st.session_state:
    st.session_state.last_analyzed_image_path = None
if 'last_analysis_result' not in st.session_state:
    st.session_state.last_analysis_result = None

def analyze_image(image, image_path, max_retries=3, rate_limit_delay=4):
    for attempt in range(max_retries):
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            response = model.generate_content([image_prompt, image])
            result_text = response.text.strip()
            
            lines = result_text.split('\n')
            is_wwtp = "Yes" if "Is it a WWTP? Yes" in lines[0] else "No"
            description = "N/A"
            circular_count = 0
            rectangular_count = 0
            circular_with_water = 0
            circular_without_water = 0
            rectangular_with_water = 0
            rectangular_without_water = 0
            
            def extract_number(text):
                match = re.search(r'\d+', text)
                return int(match.group()) if match else 0

            for line in lines:
                if "Description:" in line:
                    description = line.split('Description:')[1].strip()
                elif "Circular Features:" in line and "with Water" not in line and "without Water" not in line:
                    circular_count = extract_number(line.split(':')[1].strip())
                elif "Rectangular Features:" in line and "with Water" not in line and "without Water" not in line:
                    rectangular_count = extract_number(line.split(':')[1].strip())
                elif "Circular Features with Water:" in line:
                    circular_with_water = extract_number(line.split(':')[1].strip())
                elif "Circular Features without Water:" in line:
                    circular_without_water = extract_number(line.split(':')[1].strip())
                elif "Rectangular Features with Water:" in line:
                    rectangular_with_water = extract_number(line.split(':')[1].strip())
                elif "Rectangular Features without Water:" in line:
                    rectangular_without_water = extract_number(line.split(':')[1].strip())
            
            image_name = os.path.basename(image_path) if image_path else "Uploaded Image"
            result_dict = {
                "Image Name": image_name,
                "Is WWTP?": is_wwtp,
                "Num of Circular Features": circular_count,
                "Num of Rectangular Features": rectangular_count,
                "Num of Circular Features with Water": circular_with_water,
                "Num of Circular Features without Water": circular_without_water,
                "Num of Rectangular Features with Water": rectangular_with_water,
                "Num of Rectangular Features without Water": rectangular_without_water,
                "Description": description,
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Raw Text": result_text
            }
            
            st.session_state.last_analyzed_image = image
            st.session_state.last_analyzed_image_path = image_path if image_path else "Uploaded Image"
            st.session_state.last_analysis_result = result_dict
            
            message = f"Analysis of {image_name}:\n" \
                     f"Is it a WWTP? {is_wwtp}\n" \
                     f"Number of Circular Features: {circular_count}\n" \
                     f"Number of Rectangular Features: {rectangular_count}\n" \
                     f"Description: {description}\n"
            st.session_state.chat_history.append(("Bot", message))
            return True
        except exceptions.ResourceExhausted as e:
            if attempt < max_retries - 1:
                st.session_state.chat_history.append(("Bot", f"429 error, retrying in 10 seconds..."))
                time.sleep(10)
            else:
                handle_error(image_path, str(e))
                return False
        except Exception as e:
            if attempt == max_retries - 1:
                handle_error(image_path, str(e))
                return False
            time.sleep(2)
    time.sleep(rate_limit_delay)
    return True

def handle_error(image_path, error_msg):
    image_name = os.path.basename(image_path) if image_path else "Uploaded Image"
    result_dict = {
        "Image Name": image_name,
        "Is WWTP?": "N/A",
        "Num of Circular Features": 0,
        "Num of Rectangular Features": 0,
        "Num of Circular Features with Water": 0,
        "Num of Circular Features without Water": 0,
        "Num of Rectangular Features with Water": 0,
        "Num of Rectangular Features without Water": 0,
        "Description": f"Error: {error_msg}",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Raw Text": f"Failed processing {image_path}: {error_msg}"
    }
    st.session_state.last_analyzed_image = None
    st.session_state.last_analyzed_image_path = image_path if image_path else "Uploaded Image"
    st.session_state.last_analysis_result = result_dict
    
    message = f"Analysis of {image_name}:\n" \
             f"Is it a WWTP? N/A\n" \
             f"Number of Circular Features: 0\n" \
             f"Number of Rectangular Features: 0\n" \
             f"Description: Error: {error_msg}\n"
    st.session_state.chat_history.append(("Bot", message))

def retrieve_relevant_history(user_input):
    keywords = user_input.lower().split()
    relevant_history = []
    
    for sender, message in reversed(st.session_state.chat_history[-20:]):
        if any(keyword in message.lower() for keyword in keywords):
            relevant_history.append(f"{sender}: {message}")
    
    return "\n".join(reversed(relevant_history)) if relevant_history else "No relevant history found."

def handle_chat_response(user_input):
    lower_input = user_input.lower()
    
    # Handle commands
    if lower_input in ["clear"]:
        st.session_state.chat_history = []
        st.session_state.chat_history.append(("Bot", "Chat cleared"))
        return
    elif lower_input == "history":
        history = "\n".join(f"{sender}: {msg}" for sender, msg in st.session_state.chat_history[-10:])
        st.session_state.chat_history.append(("Bot", f"Recent chat history:\n{history}"))
        return
    elif lower_input == "help":
        message = "Available commands:\n" \
                 "- clear: Clear chat\n" \
                 "- history: Show recent chat history\n" \
                 "- help: Show this message\n" \
                 "- Questions about last image: Ask anything about the image content (e.g., features, objects, details)\n" \
                 "- General questions: I'll answer using chat history context"
        st.session_state.chat_history.append(("Bot", message))
        return

    # Handle image-related questions if an image exists
    if st.session_state.last_analyzed_image_path and st.session_state.last_analysis_result:
        if "circular" in lower_input and ("how many" in lower_input or "count" in lower_input or "number" in lower_input):
            count = st.session_state.last_analysis_result["Num of Circular Features"]
            message = f"The last analyzed image ({st.session_state.last_analysis_result['Image Name']}) has {count} circular features."
            st.session_state.chat_history.append(("Bot", message))
            return

        if "rectangular" in lower_input and ("how many" in lower_input or "count" in lower_input or "number" in lower_input):
            count = st.session_state.last_analysis_result["Num of Rectangular Features"]
            message = f"The last analyzed image ({st.session_state.last_analysis_result['Image Name']}) has {count} rectangular features."
            st.session_state.chat_history.append(("Bot", message))
            return

        # Any other question about the image
        if st.session_state.last_analyzed_image:
            try:
                custom_prompt = f"Analyze the image and answer the following question: {user_input}\nProvide a clear answer (yes/no if applicable) and a brief explanation.\n\nImage: {st.session_state.last_analyzed_image_path}"
                response = model.generate_content([custom_prompt, st.session_state.last_analyzed_image])
                st.session_state.chat_history.append(("Bot", response.text))
            except Exception as e:
                st.session_state.chat_history.append(("Bot", f"Sorry, I encountered an error while re-analyzing the image: {str(e)}"))
            return
        else:
            st.session_state.chat_history.append(("Bot", "No image available to analyze. Please upload an image first."))
            return

    # Handle general questions
    try:
        relevant_history = retrieve_relevant_history(user_input)
        context = f"Chat History:\n{relevant_history}\n\nQuestion: {user_input}"
        response = model.generate_content(context)
        st.session_state.chat_history.append(("Bot", response.text))
    except Exception as e:
        st.session_state.chat_history.append(("Bot", f"Sorry, I encountered an error: {str(e)}"))

# Streamlit App Layout
st.title("WWTP Analysis Chatbot")

# Image Upload Section
st.subheader("Upload an Image")
uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "png", "jpeg", "tif", "tiff"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_column_width=True)
    if st.button("Analyze Image"):
        with st.spinner("Analyzing image..."):
            success = analyze_image(image, uploaded_file.name)
            if success:
                st.success("Image analyzed successfully!")
            else:
                st.error("Failed to analyze image.")

# Chat Interface
st.subheader("Chat with the Bot")
for sender, message in st.session_state.chat_history:
    with st.chat_message(sender.lower()):
        st.write(message)

if prompt := st.chat_input("Ask a question or type a command"):
    st.session_state.chat_history.append(("You", prompt))
    with st.chat_message("you"):
        st.write(prompt)
    with st.chat_message("bot"):
        handle_chat_response(prompt)
        st.write(st.session_state.chat_history[-1][1])  # Display the latest bot response
    