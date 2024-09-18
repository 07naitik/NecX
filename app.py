import streamlit as st
import numpy as np
import pickle
from tensorflow.keras.models import load_model
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Define the scope
scope = ['https://www.googleapis.com/auth/spreadsheets']

# Load credentials from the Streamlit secrets
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

# Authorize the client
client = gspread.authorize(credentials)

# Open the Google Sheet (replace 'Your Google Sheet Name' with the actual name)
sheet = client.open('a401ventures').sheet1  # or use .worksheet('Sheet1') if needed


# Load the pre-trained model and scaler
try:
    model = load_model('risk_score_model.h5')
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
except Exception as e:
    st.write(f"Error loading model or scaler: {e}")

# Predefined environmental factors for 10 Boston pin codes (dummy data)
pin_code_data = {
    '02101': [80, 70, 40, 60, 50, 90, 55, 65, 70, 85, 75, 60],
    '02102': [85, 75, 45, 65, 55, 85, 50, 60, 65, 80, 70, 55],
    '02103': [90, 80, 50, 70, 60, 80, 45, 55, 60, 75, 65, 50],
    '02104': [75, 65, 35, 55, 45, 95, 60, 70, 75, 90, 80, 65],
    '02105': [82, 72, 42, 62, 52, 87, 57, 67, 72, 87, 77, 62],
    '02106': [88, 78, 48, 68, 58, 83, 53, 63, 68, 83, 73, 58],
    '02107': [78, 68, 38, 58, 48, 93, 63, 73, 78, 93, 83, 68],
    '02108': [92, 82, 52, 72, 62, 77, 47, 57, 62, 77, 67, 52],
    '02109': [90, 95, 30, 89, 20, 84, 10,  5, 30, 97, 91, 18], # low risk example
    '02110': [18, 14, 70, 30, 90, 23, 87, 79, 90, 26,  5, 98]  # high risk example
}

# Define a function to adjust the risk score based on medical history
def adjust_risk_score(risk_score, medical_history):
    adjustment_factor = 1 + 0.05 * sum(medical_history)
    adjusted_score = risk_score * adjustment_factor
    return min(adjusted_score, 100)  # Ensure the score doesn't exceed 100

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


# Housing Conditions
st.subheader('Housing Conditions')

mold_concerns = st.radio('10. Do you have concerns about mold, dampness, or poor ventilation in your home?', ['Yes', 'No'])
if mold_concerns == 'Yes':
    mold_description = st.text_area('If yes, please describe:', key='mold_description')

pollution_nearby = st.radio('11. Is your residence located near a major road, industrial area, or other sources of pollution?', ['Yes', 'No'])
if pollution_nearby == 'Yes':
    pollution_description = st.text_area('If yes, please specify:' , key='pollution_description')


# Lifestyle Factors
st.subheader('Lifestyle Factors')

green_space_visits = st.radio(
    '12. How often do you visit green spaces (like parks, forests) each week?',
    ['Rarely or never', '1-2 times per week', '3-4 times per week', '5 or more times per week']
)

air_purification = st.radio('13. Do you use any form of air purification in your home? (e.g., air filters)', ['Yes', 'No'])
if air_purification == 'Yes':
    purification_type = st.text_input('If yes, what type(s)?')


# Noise and Light Exposure
st.subheader('Noise and Light Exposure')

neighborhood_noise = st.radio('14. Do you consider your neighborhood to be noisy?', ['Yes', 'No'])
if neighborhood_noise == 'Yes':
    noise_sources = st.text_area('If yes, what are the main sources of noise?' , key='noise_sources')

artificial_light = st.radio('15. Are you exposed to high levels of artificial light at night?', ['Yes', 'No'])
if artificial_light == 'Yes':
    light_description = st.text_area('If yes, please describe:' , key='light_description')


# General Questions
st.subheader('General Questions')

environmental_issue = st.text_area('16. In your opinion, what is the most significant environmental issue affecting your health?' , key='environmental_issue')
additional_comments = st.text_area('17. Any additional comments or concerns regarding your health and environment?' , key='additional_comments')



# Calculate the risk score
if st.button('Calculate Risk Score'):
    try:
        # Get the environmental factors based on pin code
        env_factors = pin_code_data[pin_code]
        
        # Standardize the environmental factors
        env_factors_scaled = scaler.transform([env_factors])
        
        # Predict the base risk score
        base_risk_score = model.predict(env_factors_scaled)[0][0]
        
        # Adjust the risk score based on medical history
        # final_risk_score = adjust_risk_score(base_risk_score, medical_history)
        final_risk_score = base_risk_score
        
        # Display the final risk score
        st.subheader(f'Your Health Risk Score: {final_risk_score:.2f}')
    except Exception as e:
        st.write(f"Error during prediction: {e}")


    # Collect all the inputs into a dictionary
    data = {
        'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Pin Code': pin_code,
        'Age': age,
        'Gender': gender,
        'Years Residence': years_residence,
        'Respiratory Illnesses': ', '.join(respiratory_illnesses),
        'Other Respiratory Illness': other_respiratory_illness,
        'Chronic Conditions': chronic_conditions,
        'Healthcare Visits': healthcare_visits,
        'Air Quality': air_quality,
        'Exposed to Smoke': exposed_to_smoke,
        'Smoke Frequency': smoke_frequency if exposed_to_smoke == 'Yes' else '',
        'Mold Concerns': mold_concerns,
        'Mold Description': mold_description if mold_concerns == 'Yes' else '',
        'Pollution Nearby': pollution_nearby,
        'Pollution Description': pollution_description if pollution_nearby == 'Yes' else '',
        'Green Space Visits': green_space_visits,
        'Air Purification': air_purification,
        'Purification Type': purification_type if air_purification == 'Yes' else '',
        'Neighborhood Noise': neighborhood_noise,
        'Noise Sources': noise_sources if neighborhood_noise == 'Yes' else '',
        'Artificial Light': artificial_light,
        'Light Description': light_description if artificial_light == 'Yes' else '',
        'Environmental Issue': environmental_issue,
        'Additional Comments': additional_comments,
        'Risk Score': final_risk_score
    }

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

