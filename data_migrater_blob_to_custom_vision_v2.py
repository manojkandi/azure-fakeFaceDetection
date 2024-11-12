import logging
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from msrest.authentication import ApiKeyCredentials

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

    
# Azure Storage setup
connection_string = "DefaultEndpointsProtocol=https;AccountName=realfakeimages;AccountKey=HbneupGzTo2EMbBZskGwaNcJxmVBWxf1vs/Ufqr0cZ+BmgYVu2ilwDa0+Mel3LVUbvveFMobX7d++AStf/xGOA==;EndpointSuffix=core.windows.net"  
container_name = "images"  

# Create BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Check if container exists
try:
    container_client = blob_service_client.get_container_client(container_name)
    container_properties = container_client.get_container_properties()
    print(f"Container '{container_name}' exists and is accessible.")
except Exception as e:
    print(f"Error: {e}")
    exit(1)

# Azure Custom Vision setup
ENDPOINT = "https://azurecustomvisionp2.cognitiveservices.azure.com/"  
training_key = "d3d4bfe8d7334d72b3bc194c9411c64e"  
project_id = "e79bb460-59e6-4a72-a7cd-e8501b29d011"  

# Create CustomVisionTrainingClient
credentials = ApiKeyCredentials(in_headers={"Training-key": training_key})
trainer = CustomVisionTrainingClient(ENDPOINT, credentials)

# Define the function to create or retrieve the tag
def get_or_create_tag(trainer, project_id, tag_name):
    # Get the existing tags in the project
    tags = trainer.get_tags(project_id)
    
    # Search for a tag with the matching name
    for tag in tags:
        if tag.name == tag_name:
            return tag  # Return the existing tag
    
    # If the tag doesn't exist, create it
    return trainer.create_tag(project_id, tag_name)

# Create or get the 'Real' and 'Fake' tags
tag_real = get_or_create_tag(trainer, project_id, 'Real')
tag_fake = get_or_create_tag(trainer, project_id, 'Fake')

# Upload images from Azure Blob Storage to Custom Vision
for blob in container_client.list_blobs():
    blob_client = container_client.get_blob_client(blob.name)
    download_stream = blob_client.download_blob()
    image_data = download_stream.readall()

    if "Real" in blob.name:
        print(f"Uploading {blob.name} as Real")
        trainer.create_images_from_data(project_id, image_data, tag_ids=[tag_real.id])
    elif "Fake" in blob.name:
        print(f"Uploading {blob.name} as Fake")
        trainer.create_images_from_data(project_id, image_data, tag_ids=[tag_fake.id])

print("Image upload complete.")
