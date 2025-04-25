import os
# Set environment variables before importing any modules
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["STREAMLIT_SERVER_WATCH_FILES"] = "false"

# Import subprocess to run streamlit
import subprocess
import sys

if __name__ == "__main__":
    # Run the app.py file with streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])