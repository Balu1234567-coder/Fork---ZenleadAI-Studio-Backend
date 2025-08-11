import requests
import json
from urllib.parse import quote

class ImageSearcher:
    def __init__(self, api_key, cse_id):
        self.api_key = api_key  # Your Custom Search API Key (not Generative Language API)
        self.cse_id = cse_id    # Your Custom Search Engine ID
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search_images(self, topic, num_images=10):
        """
        Search for images based on topic
        """
        params = {
            'q': topic,
            'cx': self.cse_id,
            'key': self.api_key,
            'searchType': 'image',
            'num': min(num_images, 10),  # Max 10 per request
            'fileType': 'jpg,png',       # Preferred formats
            'imgSize': 'medium',         # Good balance of quality/size
            'safe': 'active'             # Safe search
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return self.process_results(data)
            
        except requests.exceptions.RequestException as e:
            print(f"API Request Error: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}")
            return []
    
    def process_results(self, data):
        """
        Extract relevant image information
        """
        images = []
        items = data.get('items', [])
        
        for item in items:
            image_info = {
                'title': item.get('title', ''),
                'image_url': item.get('link', ''),
                'thumbnail_url': item.get('image', {}).get('thumbnailLink', ''),
                'width': item.get('image', {}).get('width', 0),
                'height': item.get('image', {}).get('height', 0),
                'context_url': item.get('image', {}).get('contextLink', ''),
                'file_format': item.get('fileFormat', '')
            }
            images.append(image_info)
        
        return images
    
    def display_results(self, images, topic):
        """
        Display search results in a readable format
        """
        print(f"\n🔍 Found {len(images)} images for: '{topic}'\n")
        print("-" * 80)
        
        for i, img in enumerate(images, 1):
            print(f"{i}. {img['title']}")
            print(f"   📸 Image URL: {img['image_url']}")
            print(f"   🖼️  Thumbnail: {img['thumbnail_url']}")
            print(f"   📏 Size: {img['width']}x{img['height']}")
            print(f"   🌐 Source: {img['context_url']}")
            print("-" * 80)

# Usage Example
def main():
    # Replace with your actual credentials
    API_KEY = "AIzaSyDeu1TlQvvtapu9hBg-d9hDB-Mr_S7mx7k"  # NOT the Generative Language API key
    CSE_ID = "a274cb56528ef4919"        # From Google Custom Search Console
    
    # Initialize the searcher
    searcher = ImageSearcher(API_KEY, CSE_ID)
    
    # Interactive search
    while True:
        topic = input("\nEnter a topic to search for images (or 'quit' to exit): ")
        
        if topic.lower() in ['quit', 'exit', 'q']:
            break
        
        if not topic.strip():
            continue
        
        print(f"Searching for images about '{topic}'...")
        images = searcher.search_images(topic)
        
        if images:
            searcher.display_results(images, topic)
            
            # Option to download images
            download = input("\nWould you like to download these images? (y/n): ")
            if download.lower() == 'y':
                download_images(images, topic)
        else:
            print("No images found or API error occurred.")

def download_images(images, topic):
    """
    Download images to local folder
    """
    import os
    from urllib.parse import urlparse
    
    # Create folder for topic
    folder_name = topic.replace(' ', '_').replace('/', '_')
    os.makedirs(f'images/{folder_name}', exist_ok=True)
    
    for i, img in enumerate(images, 1):
        try:
            response = requests.get(img['image_url'], timeout=10)
            if response.status_code == 200:
                # Get file extension from URL or use jpg as default
                parsed_url = urlparse(img['image_url'])
                ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
                
                filename = f'images/{folder_name}/image_{i}{ext}'
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded: {filename}")
            else:
                print(f"❌ Failed to download image {i}")
        except Exception as e:
            print(f"❌ Error downloading image {i}: {e}")

if __name__ == "__main__":
    main()
