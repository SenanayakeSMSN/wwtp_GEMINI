import google.generativeai as genai
from PIL import Image
import os
import streamlit as st
import logging
import time
from google.api_core import exceptions

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

# Streamlit App
def main():
    st.title("WWTP Image Analyzer")
    
    # File uploader
    uploaded_file = st.file_uploader("Upload an image", type=['jpg', 'jpeg', 'png', 'tif', 'tiff'])
    
    if uploaded_file is not None:
        # Display uploaded image
        st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
        
        # Analyze button
        if st.button("Analyze"):
            with st.spinner("Analyzing..."):
                # Save uploaded file temporarily
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # Analyze the image
                result = analyze_image(temp_file_path)
                
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                
                # Display results
                if result["Is WWTP?"] == "Yes":
                    st.write("### Analysis Results")
                    st.write(f"**Description:** {result['Description']}")
                    st.write(f"**Circular objects with water:** {result['Circular Features with Water']}")
                    st.write(f"**Circular objects without water:** {result['Circular Features without Water']}")
                    st.write(f"**Rectangular objects with water:** {result['Rectangular Features with Water']}")
                    st.write(f"**Rectangular objects without water:** {result['Rectangular Features without Water']}")
                elif result["Is WWTP?"] == "No":
                    st.write("### Analysis Results")
                    st.write(f"This is not a WWTP.")
                    st.write(f"**Description:** {result['Description']}")
                else:
                    st.write("### Analysis Results")
                    st.write(f"**Error:** {result['Description']}")

if __name__ == "__main__":
    main()