import streamlit as st
from datetime import date
import os
from geopy.geocoders import Nominatim
import folium
from streamlit_folium import st_folium

# --- LangChain Imports ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ------------------------------
# 1️⃣ Set Your API Key
# ------------------------------
# WARNING: Hardcoding API keys is not recommended. Use secrets management for production.
API_KEY = "AIzaSyAWa1kMHQCbJGEkb8sUSmtkiLw6zjpoc1E"
# Setting the API key for LangChain
os.environ["GOOGLE_API_KEY"] = API_KEY

# ------------------------------
# 2️⃣ Streamlit Page Config
# ------------------------------
st.set_page_config(
    page_title="🌍 AI Travel Planner",
    page_icon="🧳",
    layout="centered"
)

# --- FIX 1: Initialize Session State ---
# This ensures the variable exists across reruns
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
if 'destination_for_map' not in st.session_state:
    st.session_state.destination_for_map = ""


st.title("🌍 AI Smart Travel Planner")
st.write("Plan your trip with personalized recommendations powered by LangChain & Gemini.")

# ------------------------------
# 3️⃣ User Inputs
# ------------------------------
destination = st.text_input("🏙️ Destination", placeholder="e.g., Paris")
start_date = st.date_input("📅 Start date", value=None, min_value=date.today())
duration = st.number_input("🕒 Duration (days)", min_value=1, step=1, value=5)
budget_level = st.selectbox("💰 Budget level", ["tight", "moderate", "flexible"])
stay_type = st.selectbox("🏠 Stay type", ["hostel", "hotel", "resort", "homestay"])
interests = st.text_input("🎯 Interests (comma-separated)", placeholder="e.g., food, monuments, nature, beaches")


# ------------------------------
# 4️⃣ LangChain Itinerary Generation Function
# ------------------------------
def generate_itinerary_with_langchain(destination, start_date, duration, budget_level, stay_type, interests):
    """
    Generates the itinerary by invoking a LangChain chain.
    """
    # 1. Define the Prompt Template
    prompt_template_str = """
You are a professional AI travel planner. Your responses should be helpful, friendly, and engaging.

Create a detailed {duration}-day travel itinerary for {destination}, {start_date_str}.
The user has a '{budget_level}' budget and prefers to stay in a '{stay_type}'.
Their interests are: '{interests}'.

Your itinerary should include:
1️⃣ A day-wise plan with specific suggestions for morning, afternoon, and evening activities.
2️⃣ Recommendations for transportation within the destination (e.g., metro, bus, ride-sharing).
3️⃣ Suggestions for accommodation based on the user's preference and budget.
4️⃣ A list of local foods and unique experiences they shouldn't miss.
5️⃣ An estimated total cost breakdown (accommodation, food, activities, transport).

Format the entire output beautifully using emojis, bullet points, and clear, readable spacing. Make it look like a professional travel guide.
"""
    prompt_template = ChatPromptTemplate.from_template(prompt_template_str)

    # 2. Initialize the LLM with the user-specified model name
    llm = ChatGoogleGenerativeAI(model="gemini-pro-latest", temperature=0.7)

    # 3. Define the Output Parser
    output_parser = StrOutputParser()

    # 4. Create the Chain
    chain = prompt_template | llm | output_parser

    # Format the start date for the prompt
    start_date_str = f"starting on {start_date.strftime('%B %d, %Y')}" if start_date else ""

    try:
        # 5. Invoke the Chain with user inputs
        itinerary = chain.invoke({
            "duration": duration,
            "destination": destination,
            "start_date_str": start_date_str,
            "budget_level": budget_level,
            "stay_type": stay_type,
            "interests": interests
        })
        return itinerary
    except Exception as e:
        st.error(f"⚠️ An error occurred while generating the itinerary: {e}")
        return None

# ------------------------------
# 5️⃣ Get Coordinates Function (No change)
# ------------------------------
def get_coordinates(place_name):
    """
    Geocodes a place name to get its latitude and longitude.
    """
    try:
        geolocator = Nominatim(user_agent="ai_travel_planner")
        location = geolocator.geocode(place_name)
        if location:
            return (location.latitude, location.longitude)
    except Exception as e:
        st.warning(f"Could not retrieve coordinates. Map may not be accurate. Error: {e}")
    return None

# ------------------------------
# 6️⃣ Generate Button Logic
# ------------------------------
if st.button("🚀 Generate Itinerary", type="primary"):
    if not destination.strip():
        st.warning("Please enter a destination before generating your itinerary.")
    else:
        with st.spinner("Crafting your perfect itinerary with LangChain... ⛓️"):
            itinerary_result = generate_itinerary_with_langchain(
                destination, start_date, duration, budget_level, stay_type, interests
            )
            # --- FIX 2: Save the result to Session State ---
            st.session_state.itinerary = itinerary_result
            st.session_state.destination_for_map = destination


# ------------------------------
# 7️⃣ Display Logic (Now outside the button block)
# ------------------------------
# --- FIX 3: Display from Session State if it exists ---
if st.session_state.itinerary:
    st.success("✅ Your personalized itinerary is ready!")
    st.markdown(st.session_state.itinerary)

    # --- Interactive Map Display using Folium ---
    st.markdown("---")
    st.subheader("📍 Interactive Map")
    coords = get_coordinates(st.session_state.destination_for_map)

    if coords:
        m = folium.Map(location=coords, zoom_start=13)
        folium.Marker(coords, popup=st.session_state.destination_for_map, tooltip=st.session_state.destination_for_map).add_to(m)
        st_folium(m, width=700, height=500)
    else:
        st.warning("Could not generate a map for the specified destination.")

    # Download button
    st.download_button(
        "📥 Download Itinerary",
        data=st.session_state.itinerary,
        file_name=f"{st.session_state.destination_for_map.replace(' ', '_')}_itinerary.txt",
        mime="text/plain"
    )

# ------------------------------
# 8️⃣ Footer
# ------------------------------
st.markdown("---")
st.caption("✨ Built with LangChain & Gemini | A project by CodeWithAyush18")

