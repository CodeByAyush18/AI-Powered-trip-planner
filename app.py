import streamlit as st
from datetime import date
import google.generativeai as genai
import json
import pandas as pd
import pydeck as pdk
import re

# ------------------------------
# 1️ Set Your API Key & Page Config
# ------------------------------

API_KEY = "AIzaSyAQMAsTLl5cM1OuG-XZBmg5p38K_rQhJfA" 


try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    st.error(f"Failed to configure API key: {e}", icon="🔑")

st.set_page_config(
    page_title="🌍 AI Travel Planner",
    page_icon="🧳",
    layout="wide" 
)

st.title("🌍 AI Smart Travel Planner")
st.write("Plan your trip with personalized recommendations and an interactive map, powered by Gemini AI.")

# ------------------------------
# 2️ User Inputs (in a sidebar)
# ------------------------------
with st.sidebar:
    st.header("⚙️ Your Trip Details")
    destination = st.text_input("🏙️ Destination", placeholder="e.g., Paris, France")
    start_date = st.date_input("📅 Start date", value=None, min_value=date.today())
    duration = st.number_input("🕒 Duration (days)", min_value=1, step=1, value=5)
    budget_level = st.selectbox("💰 Budget level", ["tight", "moderate", "flexible"])
    stay_type = st.selectbox("🏠 Stay type", ["hostel", "hotel", "resort", "homestay"])
    interests = st.text_input("🎯 Interests", placeholder="e.g., food, museums, hiking")


# 3️ Build Prompt with JSON Instruction 

def build_prompt(destination, start_date, duration, budget_level, stay_type, interests):
    start_date_str = f"starting on {start_date.strftime('%B %d, %Y')}" if start_date else ""

  
    main_prompt = f"""
You are a professional AI travel planner. Your responses should be helpful, friendly, and engaging.

Create a detailed {duration}-day travel itinerary for {destination}, {start_date_str}.
The user has a '{budget_level}' budget and prefers to stay in a '{stay_type}'.
Their interests are: '{interests}'.

Your itinerary should include:
1. A day-wise plan with specific suggestions for morning, afternoon, and evening activities.
2. Recommendations for transportation within the destination.
3. Suggestions for accommodation based on the user's preference and budget.
4. A list of local foods and unique experiences they shouldn't miss.
5. An estimated total cost breakdown.

Format the text output beautifully using emojis and markdown.
"""

 
    json_instruction = """
### IMPORTANT ###
Finally, embed a single JSON object at the very end of your response, enclosed in ```json ... ```. This JSON should contain a list of key locations mentioned. Each location must have "name", "day", "lat", and "lon".

Example JSON format:
```json
{
  "locations": [
    { "name": "Eiffel Tower", "day": 1, "lat": 48.8584, "lon": 2.2945 },
    { "name": "Louvre Museum", "day": 2, "lat": 48.8606, "lon": 2.3376 }
  ]
}"""
    return main_prompt + json_instruction
# ------------------------------
# 4️ Generate Itinerary & Parse Response
# ------------------------------
def generate_itinerary(prompt):
    try:
        model = genai.GenerativeModel('gemini-pro-latest')
        response = model.generate_content(prompt)
        full_text = response.text
        locations = None


        match = re.search(r"```json\s*(\{.*?\})\s*```|(\{.*locations.*?\})", full_text, re.DOTALL)
        
        if match:
          
            json_str = match.group(1) if match.group(1) else match.group(2)
            
            try:
                data = json.loads(json_str)
                locations = data.get("locations")
                

                clean_text = full_text.replace(match.group(0), "").strip()
                
                return clean_text, locations
            except (json.JSONDecodeError, KeyError) as e:
                st.warning(f"Found a JSON-like block but could not parse it. Displaying full text. Error: {e}")
                return full_text, None 

        return full_text, None

    except Exception as e:
        st.error(f"⚠️ An error occurred while contacting the API: {e}")
        return None, None

# 5️ Generate Button & Display

if st.sidebar.button("🚀 Generate Itinerary", type="primary"):
    if not destination.strip():
        st.warning("Please enter a destination.")
    else:
        with st.spinner("Crafting your perfect itinerary... This may take a moment. 🧳"):
            prompt = build_prompt(destination, start_date, duration, budget_level, stay_type, interests)
            itinerary_text, locations = generate_itinerary(prompt)

            if itinerary_text:
                st.success("✅ Your personalized itinerary is ready!")
                
                col1, col2 = st.columns([1, 1.2])

                with col1:
                    st.subheader("📍 Interactive Map")
                    if locations:
                        df = pd.DataFrame(locations)
                        df['lat'] = pd.to_numeric(df['lat'])
                        df['lon'] = pd.to_numeric(df['lon'])

                        st.map(df)
                    else:
                        st.info("No location data was generated to display on the map.")

                with col2:
                    st.subheader("📝 Your Itinerary")
                    st.markdown(itinerary_text)
                    st.download_button(
                        "📥 Download Itinerary",
                        data=itinerary_text,
                        file_name=f"{destination.replace(' ', '_')}_itinerary.txt"
                    )
