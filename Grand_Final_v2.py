import io
import os
import sys
import pyodbc  # Required for SQL Server connection
import streamlit as st
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.prediction.models import Prediction
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import ApiKeyCredentials
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, ResultReason
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential
from PIL import Image

#  SQL Server connection details
conn_str = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=p2analysisresults.database.windows.net;'  # SQL Server name
    'DATABASE=p2analysisdatabase;'  #  database name
    'UID=BharathReddy;'  # SQL Server username
    'PWD=Bharath@2001;'  # SQL Server password
)

# Connect to SQL Server
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Create a new table to store image analysis results
cursor.execute('''\
    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='image_analysis_results' AND xtype='U')
    CREATE TABLE image_analysis_results (
        id INT IDENTITY(1,1) PRIMARY KEY,
        image_path NVARCHAR(255),
        predicted_class NVARCHAR(50),
        description NVARCHAR(MAX),
        probability FLOAT
    )
''')
conn.commit()

# Azure Cognitive Services credentials and clients (updated)
CUSTOM_VISION_ENDPOINT = "https://p2custvisrev-prediction.cognitiveservices.azure.com/"
CUSTOM_VISION_PREDICTION_KEY = "cb159946ec39483e9a4afefbd3d4cf2a"
CUSTOM_VISION_PROJECT_ID = "e79bb460-59e6-4a72-a7cd-e8501b29d011"
CUSTOM_VISION_PUBLISHED_NAME = "FakeImageClassification"

COMPUTER_VISION_ENDPOINT = "https://p2-computervis-rev.cognitiveservices.azure.com/"
COMPUTER_VISION_KEY = "570650860c2f451fba4a1a12ccd854fd"

SPEECH_KEY = "fb85edfbfbe34a9d90e7e53c0638fc85"

TRANSLATOR_ENDPOINT = "https://p2-translate-rev.cognitiveservices.azure.com/"
TRANSLATOR_KEY = "f9bfc88701054947bd983509993a9d3b"

# Authenticate clients
custom_vision_credentials = ApiKeyCredentials(in_headers={"Prediction-key": CUSTOM_VISION_PREDICTION_KEY})
custom_vision_client = CustomVisionPredictionClient(CUSTOM_VISION_ENDPOINT, custom_vision_credentials)

computervision_credentials = ApiKeyCredentials(in_headers={"Ocp-Apim-Subscription-Key": COMPUTER_VISION_KEY})
computervision_client = ComputerVisionClient(COMPUTER_VISION_ENDPOINT, computervision_credentials)

speech_config = SpeechConfig(subscription=SPEECH_KEY, region="eastus")

translator_client = TextTranslationClient(endpoint=TRANSLATOR_ENDPOINT, credential=AzureKeyCredential(TRANSLATOR_KEY))

def classify_image(image_path):
    """Classify the image using Custom Vision API."""
    with open(image_path, "rb") as image_data:
        results = custom_vision_client.classify_image(
            project_id=CUSTOM_VISION_PROJECT_ID,
            published_name=CUSTOM_VISION_PUBLISHED_NAME,
            image_data=image_data
        )

    # Print classification results
    for prediction in results.predictions:
        print(f"{prediction.tag_name}: {prediction.probability:.2f}")

    # Determine the classification result
    if results.predictions:
        top_prediction = max(results.predictions, key=lambda x: x.probability)
        if top_prediction.probability > 0.5:
            return top_prediction.tag_name, top_prediction.probability
    return None, None

def describe_image(image_path):
    """Describe the image using Computer Vision API."""
    with open(image_path, "rb") as image_data:
        description_results = computervision_client.describe_image_in_stream(
            image_data,
            visual_features=["Description"]
        )

    # Print the image description
    if description_results.captions:
        description_message = "Description: " + ", ".join(
            [f"{caption.text} (confidence: {caption.confidence:.2f})" for caption in description_results.captions]
        )
        return description_message
    return "No descriptions available."

def insert_into_sql(image_path, predicted_class, description, probability):
    """Insert the image analysis results into the new SQL Server table."""
    cursor.execute('''\
        INSERT INTO image_analysis_results (image_path, predicted_class, description, probability)
        VALUES (?, ?, ?, ?)
    ''', (image_path, predicted_class, description, probability))
    conn.commit()

def synthesize_speech(text, language="en"):
    """Convert text to speech using Azure Speech Service.""" 
    language_map = {
        "en": "en-US-JennyNeural",       # English
        "hi": "hi-IN-SwaraNeural",       # Hindi
        "te": "te-IN-MohanNeural",       # Telugu
        "ta": "ta-IN-PallaviNeural"      # Tamil
    }
    
    if language not in language_map:
        return
    
    speech_config.speech_synthesis_voice_name = language_map[language]
    speech_synthesizer = SpeechSynthesizer(speech_config=speech_config)
    
    result = speech_synthesizer.speak_text(text)
    
    if result.reason == ResultReason.SynthesizingAudioCompleted:
        print(f"Successfully synthesized the text to speech: {text}")

def translate_text(text, target_language="hi"):
    """Translate text to the target language using Azure Translator Service."""
    body = [{"text": text}]
    
    response = translator_client.translate(content=body, to=[target_language])
    
    translation = response[0].translations[0].text
    return translation

# Set page config to use a white background
st.set_page_config(
    page_title="Image Analysis App",
    page_icon="🖼️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS to center content and style buttons
st.markdown("""
    <style>
    .centered {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    .stButton > button {
        display: block;
        margin: 0 auto;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Image Classification and Description with Audio Output</h1>", unsafe_allow_html=True)

# Add 3-line description
st.markdown("""
    <p style='text-align: center;'>
    This app allows users to classify images as real or fake using Azure's Custom Vision AI model.<br>
    It provides a description of the uploaded image using the Computer Vision API.<br>
    You can also listen to the results in multiple languages using text-to-speech and translation services.
    </p>
""", unsafe_allow_html=True)

# Centered container
with st.container():
    st.markdown("<div class='centered'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Save the uploaded file to a temporary path
        temp_image_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)  # Create a temp directory if it doesn't exist
        
        with open(temp_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Display the image with reduced dimensions (e.g., width of 300 pixels)
        st.image(uploaded_file, caption="Uploaded Image", width=300)

        try:
            # Classify the image
            predicted_class, probability = classify_image(temp_image_path)
            
            # Describe the image
            description = describe_image(temp_image_path)
            
            if predicted_class and probability is not None:
                st.write(f"Predicted Class: {predicted_class} (Probability: {probability:.2f})")
                st.write(f"Description: {description}")

                # Save results to SQL
                insert_into_sql(temp_image_path, predicted_class, description, probability)

                # Convert to speech
                text = f"The image is predicted to be {predicted_class} with a probability of {probability:.2f}. {description}"
                
                # Center buttons for audio controls
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Play in English"):
                        synthesize_speech(text, language="en")
                with col2:
                    if st.button("Stop Audio"):
                        # Call your stop_audio function here
                        pass

                # Language translation and speech options
                target_language = st.selectbox("Select language for translation", 
                                                ["English (en)", "हिन्दी (hi)", "తెలుగు (te)", "தமிழ் (ta)"])

                target_language_code = target_language.split("(")[-1].strip(")")

                if target_language_code != "en":
                    translated_text = translate_text(text, target_language_code)
                    st.write(f"Translated Text: {translated_text}")

                    # Play the translated text as speech
                    if st.button(f"Play in {target_language.split()[0]}"):
                        synthesize_speech(translated_text, language=target_language_code)
        
        except Exception as e:
            st.write(f"Error processing the image: {str(e)}")
