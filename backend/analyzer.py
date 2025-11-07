import os
from dotenv import load_dotenv
from jd_analyzer import jd_analyzer  # Changed to relative import since we're in backend folder
import asyncio

# Load environment variables and print debug info
load_dotenv()
print("Debug: GOOGLE_API_KEY present:", "GOOGLE_API_KEY" in os.environ)
if "GOOGLE_API_KEY" in os.environ:
    print("Debug: API key length:", len(os.environ["GOOGLE_API_KEY"]))

# Sample job description text
jd_text = """
We are looking for a Machine Learning Engineer with 3+ years of experience.
Must be proficient in Python, TensorFlow, and data preprocessing.
Experience with cloud platforms like AWS or Azure is a plus.
Full-time position.
"""

# Mock the LangGraph state input
state = {"job_description": jd_text}

# Call the JD analyzer directly (it's an async function)
async def main():
    output = await jd_analyzer(state)
    return output

# Run the async function and display result
output = asyncio.run(main())
import json
print(json.dumps(output, indent=4))
