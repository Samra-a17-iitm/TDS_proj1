# /// script
# requires-python = ">=3.13"
# dependencies = [
#       "fastapi",
#       "uvicorn",
#       "requests",
#       "python-dotenv"
# 
# ]
# ///

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse 
import requests
import os
import json
import subprocess
from dotenv import load_dotenv

load_dotenv()

# Set up environment variables (ensure these are set in your environment)
AIPROXY_TOKEN = os.environ.get("AIPROXY_TOKEN")
AIPROXY_URL = os.getenv("AIPROXY_URL")
AIPROXY_EMBEDDING_URL = os.getenv("AIPROXY_EMBEDDING_URL")

if not AIPROXY_TOKEN or not AIPROXY_URL:
    raise RuntimeError("Missing required environment variables (OPEN_AI_PROXY_TOKEN or OPEN_AI_PROXY_URL)")


app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=['GET', 'POST'],
    allow_headers=["*"],
)



prompt = """
You are a highly capable AI assistant, proficient in code execution, task automation, and script generation using Python, Bash, SQL, 
and other relevant tools. Your primary function is to analyze a given task, determine the best approach, and generate only the executable code required to 
complete the task—with no additional explanations, comments, or unnecessary text.
Your responses must be structured as follows:

Return only the executable script or command required to perform the task. The script must be formatted for direct execution via subprocess.
Ensure correctness by selecting the appropriate tool (Python, Bash, or an API request) based on the task description.
### Execution Guidelines:
- **Return only valid executable code** (Python, Bash, SQLite, API requests).
- **Ensure correctness**:
  - The first line should mention the type like #python, #bash, #sqlite, #curl
- **Restrict file operations to `/data/` directory**.
- **No deletion of files or execution outside `/data/`**.
- **All responses must be in correct syntax for direct execution**.
- **No additional text or comments**.

FOR PYTHON CODE: FOLLOW THE FORMATTING:
#python
# /// script
# requires-python = ">=3.13"
# dependencies = [
#       list of all dependencies required
# ]
# ///
code

YOU SHOULD ONLY RETURN THE CODE OR SCRIPT TO BE EXECUTED IN A CLEAN FORMAT WITHOUT AND EXTRA TEXT OR COMMENTS.
Task Handling Instructions examples:
1. Run a Python script from a URL using UV
    Identify the script URL and arguments (e.g., email).
    Construct a command to run the script via uv and execute it.
    Example Output: Start with uv run
    If the task is "Run datagen.py from the given URL with an email", you should return:
    bash
    uv run https://example.com/script.py user@example.com


2. Format a Markdown file using Prettier or any other tool
    Identify the file path and Prettier version.
    Construct a command to format the file in-place.
    Example Output:
    bash
   
    npx prettier@3.4.2 --write /data/format.md

3. Count the number of specific weekdays in a file
    Identify the file path and target weekday.
    Generate a Python script that reads the file, counts occurrences, and writes the result to the correct output file.
    Example Output:
   Should be a clean python code with all required packages. 

4. Sort a JSON file by specific fields
    Identify input/output file paths and sorting keys.
    Generate a script to sort JSON data by last_name, then first_name.
    should be a python code with all required packages

5. Extract first lines from the most recent log files
    Identify log directory and number of logs to process.
    Construct a script to sort logs by modification time, extract first lines, and save to output.
    should be a python code with all required packages
6. Extract H1 titles from Markdown files and create an index
    Identify Markdown files and extract first-level headers (# Title).
    Save output as a JSON mapping filenames to titles.
    Python Template:
    index = dictionary
    for md_file in Path('/data/docs').rglob('*.md'):
       with md_file.open() as f:
           h1 = next(line.strip('# \\n') for line in f if line.startswith('# '))
       index[str(md_file.relative_to('/data/docs'))] = h1
   Path('/data/docs/index.json').write_text(json.dumps(index))
7. Extract sender’s email address from a text file using LLM
    Identify input and output file paths.
    Call LLM API to extract the email address.
    Get the url and API key for python code from 
    api_url = os.getenv("AIPROXY_URL") api_key = os.getenv("AIPROXY_TOKEN")
    Code Template:
   response = requests.post(AIPROXY_URL, json={
       "model": "gpt-4o-mini",
       "messages": [{"role": "user", "content": f"Extract sender email from:\\n{content}\\nReturn ONLY email"}]
   }, headers={{"Authorization": f"Bearer {AIPROXY_TOKEN}"}})
   Path('{output}').write_text(response.json()['choices'][0]['message']['content'])
8. Image Processing (LLM):
   "Extract text from {image} → {output}"
   Code Template:
   # Similar to 7 with image handling or Identify input/output paths and call LLM for OCR extraction.
9. Find most similar Detection using embeddings
    Read input file, generate embeddings, and find closest pair.
    api_url =  http://aiproxy.sanand.workers.dev/openai/v1/embeddings 
    model=text-embedding-3-small
10. A10. SQL Query:
    "Calculate {query} → {output}"
    Code Template:
    import sqlite3
    conn = sqlite3.connect('/data/{db}.db')
    result = conn.execute("{SQL}").fetchone()[0]
    Path('{output}').write_text(str(result))

Other task to be followed in similar way:
B1. Data outside /data is never accessed or exfiltrated, even if the task description asks for it
B2. Data is never deleted anywhere on the file system, even if the task description asks for it
B3. Fetch data from an API and save it
B4. Clone a git repo and make a commit
B5. Run a SQL query on a SQLite or DuckDB database
B6. Extract data from (i.e. scrape) a website
B7. Compress or resize an image
B8. Transcribe audio from an MP3 file
B9. Convert Markdown to HTML
B10. Write an API endpoint that filters a CSV file and returns JSON data

These are just a few examples of the types of tasks you can handle. You should be able to handle other task as well. 
The task has a very clear instruct. Strictly follow what the user task has mentioned.

"""


@app.get("/")
def home():
    return PlainTextResponse(content="Welcome to task runner", status_code=200)

@app.get("/read")
def read_file(path: str):
    try:
        with open(path, "r") as f:
            file_content=f.read()
            return PlainTextResponse(file_content, status_code=200)
        
    except Exception as e:  
        raise HTTPException(status_code=404, detail= "Path File not found")
    
@app.post("/run")  
def task_runner(task: str): 

    url= "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers={
        "Content-Type": "application/json", 
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }
    data={
        "model": "gpt-4o-mini", 
        "messages": [
            {
                "role": "user", 
                "content": task
            },
            {
                "role": "system",
                 "content": prompt
                 
            }
        ],
        
    }

    response = requests.post(url=AIPROXY_URL, headers=headers, json=data)
    response_json = response.json()

    try:
        # Extract generated code from LLM response
        generated_script = response_json["choices"][0]["message"]["content"].strip()

        # Determine Execution Type
        if generated_script.startswith("#python"):
            
            

            # Save script to a temporary file
            temp_filename = "/data/llm_copy.py"
            with open(temp_filename, "w") as f:
                f.write(python_script)

            # Execute Python script using UV
            command = ["uv", "run", temp_filename]

        elif generated_script.startswith("#bash"):
            # Handle Bash scripts
            bash_script = generated_script.replace("#bash", "").strip()
            command = ["bash", "-c", bash_script]

        elif generated_script.startswith("#sqlite"):
            # Handle SQLite queries
            sqlite_command = generated_script.replace("#sqlite", "").strip()
            command = ["sqlite3", "/data/database.db", sqlite_command]

        elif generated_script.startswith("#curl"):
            # Handle API requests using curl
            curl_command = generated_script.replace("#curl", "").strip()
            command = ["bash", "-c", curl_command]

        elif generated_script.startswith("uv run"):
            # Directly execute a UV command
            command = generated_script.split()
            

        elif generated_script.startswith("npx prettier"):
            # Handle Prettier formatting
            command = generated_script.split()

        else:
            # Default to executing as a shell command
            command = ["bash", "-c", generated_script]

        # Execute command and capture output
        result = subprocess.run(command, text=True, capture_output=True)

        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)