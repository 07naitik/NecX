import streamlit as st
import numpy as np
import pickle
from tensorflow.keras.models import load_model
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

# Define the scope
scope = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Load credentials from the Streamlit secrets
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

# Authorize the client
client = gspread.authorize(credentials)

# Open the Google Sheet
spreadsheet_id = '1M3_j3bBKjIXEY1MAtg9NHLcHBXftfrpLTt7vGhjUHrQ'
sheet = client.open_by_key(spreadsheet_id).sheet1

# Define OpenWeatherMap API details
OPENWEATHERMAP_API_KEY = st.secrets["openweathermap"]["api_key"]
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Load the pre-trained model and scaler
try:
    model = load_model('risk_score_model.h5')
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
except Exception as e:
    st.write(f"Error loading model or scaler: {e}")
    
def get_weather_data(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'appid': OPENWEATHERMAP_API_KEY
    }
    response = requests.get(WEATHER_API_URL, params=params)
    data = response.json()
    if response.status_code == 200:
        return data
    else:
        st.write(f"Error fetching weather data: {data.get('message', 'Unknown error')}")
        return None

# Predefined environmental factors for 10 Boston pin codes (dummy data)
pin_code_data = {
    '02108': [80, 70, 40, 60, 50, 90, 55, 65, 70, 85, 75, 60],
    '02109': [85, 75, 45, 65, 55, 85, 50, 60, 65, 80, 70, 55],
    '02110': [90, 80, 50, 70, 60, 80, 45, 55, 60, 75, 65, 50],
    '02111': [75, 65, 35, 55, 45, 95, 60, 70, 75, 90, 80, 65],
    '02112': [82, 72, 42, 62, 52, 87, 57, 67, 72, 87, 77, 62],
    '02113': [88, 78, 48, 68, 58, 83, 53, 63, 68, 83, 73, 58],
    '02114': [78, 68, 38, 58, 48, 93, 63, 73, 78, 93, 83, 68],
    '02115': [92, 82, 52, 72, 62, 77, 47, 57, 62, 77, 67, 52],
    '02116': [90, 95, 30, 89, 20, 84, 10,  5, 30, 97, 91, 18],  # low risk example
    '02117': [18, 14, 70, 30, 90, 23, 87, 79, 90, 26,  5, 98]  # high risk example
}

boston_zip_coords = {
    "02108": {"latitude": 42.3571, "longitude": -71.0636},
    "02109": {"latitude": 42.3611, "longitude": -71.0552},
    "02110": {"latitude": 42.3576, "longitude": -71.0533},
    "02111": {"latitude": 42.3497, "longitude": -71.0603},
    "02112": {"latitude": 42.3601, "longitude": -71.0589}, 
    "02113": {"latitude": 42.3663, "longitude": -71.0544},
    "02114": {"latitude": 42.3614, "longitude": -71.0677},
    "02115": {"latitude": 42.3433, "longitude": -71.0927},
    "02116": {"latitude": 42.3496, "longitude": -71.0776},
    "02117": {"latitude": 42.3610, "longitude": -71.0580}   
}

# Page navigation handling
if 'page' not in st.session_state:
    st.session_state.page = 'landing'

if st.session_state.page == 'landing':
    st.title('Welcome to the Boston Health Risk Score Predictor')
    st.write("""
    **Description:**

    Welcome to the Boston Health Risk Score Predictor! This tool is designed to help residents of Boston assess their health risk based on various environmental and personal factors. By answering a few questions about your demographics, health history, environmental exposures, and lifestyle factors, you will receive a personalized health risk score.

    **Purpose:**

    Our aim is to provide valuable insights into how different factors can affect your health and to empower you to make informed decisions. Your participation also contributes to ongoing research aimed at improving public health outcomes in the Boston area.

    **Privacy Notice:**

    All information collected is confidential and will be used solely for research purposes. Your data will be securely stored and will not be shared with third parties.

    **Get Started:**

    Click the button below to begin the assessment.
    """)
    if st.button('Go to App'):
        st.session_state.page = 'main'

elif st.session_state.page == 'main':
    # Streamlit interface
    st.title('Boston Health Risk Score Predictor')

    # Pin code selection
    st.subheader('Enter your Boston pin code:')
    pin_code = st.selectbox('Select your pin code:', list(pin_code_data.keys()))

    # Demographic Information
    st.subheader('Demographic Information')
    age = st.number_input('1. Age:', min_value=0, max_value=120, step=1)
    gender = st.selectbox('2. Gender:', ['Male', 'Female', 'Other'])
    years_residence = st.number_input('4. Number of years living in current residence:', min_value=0, max_value=100, step=1)

    # Health History
    st.subheader('Health History')

    respiratory_illnesses = st.multiselect(
        '5. Have you ever been diagnosed with any of the following respiratory illnesses? (Select all that apply)',
        ['Asthma', 'Chronic Obstructive Pulmonary Disease (COPD)', 'Allergic Rhinitis', 'Other respiratory infections']
    )

    other_respiratory_illness = st.text_input('If "Other respiratory infections", please specify:')
    chronic_conditions = st.text_input('6. Do you have any chronic health conditions? (e.g., cardiovascular disease, diabetes) If yes, please specify:')
    healthcare_visits = st.number_input('7. How many times have you visited a healthcare provider for respiratory issues in the past year?', min_value=0, step=1)

    # Environmental Exposures
    st.subheader('Environmental Exposures')

    air_quality = st.radio(
        '8. How would you rate the air quality in your living area?',
        ['Very poor', 'Poor', 'Moderate', 'Good', 'Excellent']
    )

    exposed_to_smoke = st.radio('9. Are you exposed to tobacco smoke or do you smoke?', ['Yes', 'No'])
    if exposed_to_smoke == 'Yes':
        smoke_frequency = st.text_input('If yes, how frequently?')
    else:
        smoke_frequency = ''

    # Housing Conditions
    st.subheader('Housing Conditions')

    mold_concerns = st.radio('10. Do you have concerns about mold, dampness, or poor ventilation in your home?', ['Yes', 'No'])
    if mold_concerns == 'Yes':
        mold_description = st.text_area('If yes, please describe:', key='mold_description')
    else:
        mold_description = ''

    pollution_nearby = st.radio('11. Is your residence located near a major road, industrial area, or other sources of pollution?', ['Yes', 'No'])
    if pollution_nearby == 'Yes':
        pollution_description = st.text_area('If yes, please specify:', key='pollution_description')
    else:
        pollution_description = ''

    # Lifestyle Factors
    st.subheader('Lifestyle Factors')

    green_space_visits = st.radio(
        '12. How often do you visit green spaces (like parks, forests) each week?',
        ['Rarely or never', '1-2 times per week', '3-4 times per week', '5 or more times per week']
    )

    air_purification = st.radio('13. Do you use any form of air purification in your home? (e.g., air filters)', ['Yes', 'No'])
    if air_purification == 'Yes':
        purification_type = st.text_input('If yes, what type(s)?')
    else:
        purification_type = ''

    # Noise and Light Exposure
    st.subheader('Noise and Light Exposure')

    neighborhood_noise = st.radio('14. Do you consider your neighborhood to be noisy?', ['Yes', 'No'])
    if neighborhood_noise == 'Yes':
        noise_sources = st.text_area('If yes, what are the main sources of noise?', key='noise_sources')
    else:
        noise_sources = ''

    artificial_light = st.radio('15. Are you exposed to high levels of artificial light at night?', ['Yes', 'No'])
    if artificial_light == 'Yes':
        light_description = st.text_area('If yes, please describe:', key='light_description')
    else:
        light_description = ''

    # General Questions
    st.subheader('General Questions')

    environmental_issue = st.text_area('16. In your opinion, what is the most significant environmental issue affecting your health?', key='environmental_issue')
    additional_comments = st.text_area('17. Any additional comments or concerns regarding your health and environment?', key='additional_comments')

    # Calculate the risk score
    if st.button('Calculate Risk Score'):
        try:
            lat = boston_zip_coords[pin_code]["latitude"]
            lon = boston_zip_coords[pin_code]["longitude"]
            
            weather_data = get_weather_data(lat , lon)
            
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            
            # Get the environmental factors based on pin code
            env_factors = pin_code_data[pin_code]
            
            env_factors[4] = temperature - 250
            env_factors[1] = humidity

            # Standardize the environmental factors
            env_factors_scaled = scaler.transform([env_factors])

            # Predict the base risk score
            base_risk_score = model.predict(env_factors_scaled)[0][0]

            # Convert to native Python float
            final_risk_score = float(base_risk_score)

            # Collect all the inputs into a dictionary
            data = {
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Pin Code': pin_code,
                'Age': int(age),
                'Gender': gender,
                'Years Residence': int(years_residence),
                'Respiratory Illnesses': ', '.join(respiratory_illnesses),
                'Other Respiratory Illness': other_respiratory_illness,
                'Chronic Conditions': chronic_conditions,
                'Healthcare Visits': int(healthcare_visits),
                'Air Quality': air_quality,
                'Exposed to Smoke': exposed_to_smoke,
                'Smoke Frequency': smoke_frequency,
                'Mold Concerns': mold_concerns,
                'Mold Description': mold_description,
                'Pollution Nearby': pollution_nearby,
                'Pollution Description': pollution_description,
                'Green Space Visits': green_space_visits,
                'Air Purification': air_purification,
                'Purification Type': purification_type,
                'Neighborhood Noise': neighborhood_noise,
                'Noise Sources': noise_sources,
                'Artificial Light': artificial_light,
                'Light Description': light_description,
                'Environmental Issue': environmental_issue,
                'Additional Comments': additional_comments,
                'CURRENT TEMPERATURE (degrees C)': temperature-273,
                'CURRENT HUMIDITY (%)': humidity,
                'Risk Score': final_risk_score
            }

            # Convert any NumPy data types to native Python types
            for key, value in data.items():
                if isinstance(value, np.generic):
                    data[key] = value.item()

            # Append data to Google Sheet
            try:
                # Check if the sheet is empty
                if len(sheet.get_all_records()) == 0:
                    # Write the header row
                    sheet.append_row(list(data.keys()))

                # Append the data
                sheet.append_row(list(data.values()))
            except Exception as e:
                st.write(f"Error saving data to Google Sheet: {e}")
                
            # Display the environmental factors
            st.write("### Environmental Factors")
            st.write(f"- Current Temperature: {temperature - 273} °C")
            st.write(f"- Current Humidity: {humidity}%")
            st.write(f"- Air Quality: {env_factors[0]}")
            st.write(f"- Noise Pollution: {env_factors[2]}")
            st.write(f"- Green Spaces: {env_factors[3]}")
            st.write(f"- Housing Quality: {env_factors[5]}")
            st.write(f"- Light Pollution: {env_factors[6]}")
            st.write(f"- Traffic Density: {env_factors[7]}")
            st.write(f"- Industrial Activity: {env_factors[8]}")
            st.write(f"- Socioeconomic Factors: {env_factors[9]}")
            st.write(f"- Waste Management: {env_factors[10]}")
            st.write(f"- Radiation: {env_factors[11]}")

            # Display the final risk score
            st.subheader(f'Your Health Risk Score: {final_risk_score:.2f}')
        except Exception as e:
            st.write(f"Error during prediction: {e}")
