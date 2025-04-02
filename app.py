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
    
'''

import streamlit as st
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
   - Inlet and Outlet Structures: Look for pipes, channels, or canalsA entering (from populated/industrial areas) and exiting (to a river, lake, or ocean). Pumping stations (small buildings) may be nearby.
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

# Function to analyze image
def analyze_image(image, question=None, initial=False, max_retries=3, rate_limit_delay=4):
    result = None
    for attempt in range(max_retries):
        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            content = [question if question else prompt, image]
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
                
                result = {
                    "Is WWTP?": is_wwtp,
                    "Num of Circular Features": circular_count,
                    "Num of Rectangular Features": rectangular_count,
                    "Num of Circular Features with Water": circular_with_water,
                    "Num of Circular Features without Water": circular_without_water,
                    "Num of Rectangular Features with Water": rectangular_with_water,
                    "Num of Rectangular Features without Water": rectangular_without_water,
                    "Description": description,
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Text": result_text
                }
            else:
                result = {"Text": result_text}
            break

        except exceptions.ResourceExhausted as e:
            if attempt < max_retries - 1:
                logger.warning(f"429 error, retrying in 10 seconds...")
                time.sleep(10)
            else:
                error_msg = f"Error: {str(e)}"
                result = {"Text": error_msg}
                if initial:
                    result.update({
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
            result = {"Text": error_msg}
            if initial:
                result.update({
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
                result = {"Text": error_msg}
                if initial:
                    result.update({
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
    return result

# Streamlit app
def main():
    st.title("WWTP Chatbot Analyzer (Gemini)")

    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'results' not in st.session_state:
        st.session_state.results = []
    if 'image' not in st.session_state:
        st.session_state.image = None
    if 'image_name' not in st.session_state:
        st.session_state.image_name = None
    if 'analyzed' not in st.session_state:
        st.session_state.analyzed = False

    # Sidebar for image upload and analysis
    st.sidebar.header("Upload and Analyze Image")
    uploaded_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "tif", "tiff"])

    if uploaded_file is not None:
        # Only update image if it's a new upload
        if st.session_state.image_name != uploaded_file.name:
            st.session_state.image = Image.open(uploaded_file)
            st.session_state.image_name = uploaded_file.name
            st.session_state.chat_history.append({"sender": "System", "message": f"Image uploaded: {uploaded_file.name}"})
            st.session_state.analyzed = False  # Reset analyzed state for new image

        # Display uploaded image
        st.image(st.session_state.image, caption="Uploaded Image", use_column_width=True)

        # Analyze button
        if st.sidebar.button("Analyze"):
            with st.spinner("Analyzing image for WWTP..."):
                result = analyze_image(st.session_state.image, initial=True)
                st.session_state.chat_history.append({"sender": "Gemini", "message": result["Text"]})
                result["Image Name"] = uploaded_file.name
                st.session_state.results.append(result)
                st.session_state.analyzed = True
            st.rerun()

    # Chat interface
    st.header("Chat")
    chat_container = st.container()
    with chat_container:
        for chat in st.session_state.chat_history:
            st.write(f"**{chat['sender']}:** {chat['message']}")

    # Input for questions (only enabled after analysis)
    if st.session_state.image and st.session_state.analyzed:
        question = st.text_input("Ask a question about the image:", key="question_input")
        if st.button("Send") and question:
            with st.spinner("Processing your question..."):
                st.session_state.chat_history.append({"sender": "You", "message": question})
                result = analyze_image(st.session_state.image, question=question)
                st.session_state.chat_history.append({"sender": "Gemini", "message": result["Text"]})
            st.rerun()
    elif st.session_state.image and not st.session_state.analyzed:
        st.info("Please click 'Analyze' to process the image before asking questions.")
    else:
        st.info("Please upload an image and analyze it first.")

    # Save results
    if st.button("Save Results"):
        if not st.session_state.results:
            st.warning("No results to save yet!")
        else:
            output_file = f"geminiallimagestest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame([r for r in st.session_state.results if "Image Name" in r])
            df.to_excel(output_file, index=False)
            st.session_state.chat_history.append({"sender": "System", "message": f"Results saved to {output_file}"})
            st.success(f"Results saved to {output_file}")
            with open(output_file, "rb") as file:
                st.download_button(
                    label="Download Results",
                    data=file,
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    main()