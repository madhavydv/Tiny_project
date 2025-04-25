from dotenv import load_dotenv
import os
from transformers import AutoTokenizer

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("HUGGINGFACE_API_KEY")
print(f"API Key found: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Key: {api_key[:10]}... (first 10 characters)")

# Test API access
try:
    # Try to load a simple tokenizer
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased", use_auth_token=api_key)
    print("\nAPI test successful!")
except Exception as e:
    print(f"\nAPI test failed: {str(e)}")
