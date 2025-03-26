import google.generativeai as genai
from PIL import Image
import os
import streamlit as st
import logging
import time
from google.api_core import exceptions
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
- For all counts, provide only an integer value (e.g., 5, 10, 0). If exact counting is difficult due to resolution or overlapping features, estimate the number as an integer without additional text or qualifiers (e.g., use 20 instead of '20+' or '20 20 (approximate)').

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

# Function to analyze the image
def analyze_image(image_path, max_retries=3, rate_limit_delay=4):
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
                """Extract the first integer from a string, or return 0 if none found."""
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
                return {
                    "Is WWTP?": "N/A",
                    "Description": f"Error: {str(e)}",
                    "Circular Features": 0,
                    "Rectangular Features": 0,
                    "Circular Features with Water": 0,
                    "Circular Features without Water": 0,
                    "Rectangular Features with Water": 0,
                    "Rectangular Features without Water": 0
                }
        except Exception as e:
            if attempt == max_retries - 1:
                return {
                    "Is WWTP?": "N/A",
                    "Description": f"Error: {str(e)}",
                    "Circular Features": 0,
                    "Rectangular Features": 0,
                    "Circular Features with Water": 0,
                    "Circular Features without Water": 0,
                    "Rectangular Features with Water": 0,
                    "Rectangular Features without Water": 0
                }
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
                st.write("### Analysis Results")
                if result["Is WWTP?"] == "Yes":
                    st.write(f"**Description:** {result['Description']}")
                    st.write(f"**Circular Features:** {result['Circular Features']}")
                    st.write(f"**Rectangular Features:** {result['Rectangular Features']}")
                    st.write(f"**Circular Features with Water:** {result['Circular Features with Water']}")
                    st.write(f"**Circular Features without Water:** {result['Circular Features without Water']}")
                    st.write(f"**Rectangular Features with Water:** {result['Rectangular Features with Water']}")
                    st.write(f"**Rectangular Features without Water:** {result['Rectangular Features without Water']}")
                elif result["Is WWTP?"] == "No":
                    st.write(f"This is not a WWTP.")
                    st.write(f"**Description:** {result['Description']}")
                else:
                    st.write(f"**Error:** {result['Description']}")

if __name__ == "__main__":
    main()