# Deepfake Image Classification and Image Analysis App

This project demonstrates a comprehensive system for deepfake image classification using Azure Custom Vision and additional image analysis services. It also provides a user-friendly web app to upload, classify, describe, and interact with images using several Azure Cognitive Services such as Computer Vision, Speech, and Translation.

## Project Overview

The project contains two main components:

1. **Image Migration (`data_migrater_blob_to_custom_vision_v2.py`)**: 
   This script handles migrating images from Azure Blob Storage to Azure Custom Vision, classifying them into 'Real' and 'Fake' categories. The system fetches images stored in Azure Blob Storage, assigns appropriate tags, and uploads them to Custom Vision for classification.

2. **Image Classification (`Grand_Final_v2.py`)**: 
   This Streamlit-based web app allows users to upload images, classify them as 'Real' or 'Fake' using the Custom Vision model, and generate detailed descriptions using the Azure Computer Vision API. The app can also translate text descriptions into multiple languages and generate speech output via Azure Speech Service.

## Requirements

To run this project, you will need:

- **Python 3.x**
- **Azure SDK for Python**
- **Streamlit**
- **Pillow (PIL)**
- **ODBC Driver for SQL Server (pyodbc)**

You can install the required libraries by running:

```bash
pip install azure-storage-blob azure-cognitiveservices-vision-customvision azure-cognitiveservices-speech azure-ai-translation-text azure-cognitiveservices-vision-computervision pyodbc streamlit pillow
