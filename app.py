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




app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=['GET', 'POST'],
    allow_headers=["*"],
)

# Define the response format schema for structured JSON output
# Define JSON response format for structured execution
# Response format schema for structured JSON output
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "task_runner",
        "schema": {
            "type": "object",
            "properties": {
                "script_type": {
                    "type": "string",
                    "enum": ["python", "bash", "command"],
                    "description": "Type of script to execute"
                },
                "script_code": {
                    "type": "string",
                    "description": "Script or command to execute"
                },
                "execution_type": {
                    "type": "string",
                    "enum": ["uv", "shell", "direct"],
                    "description": "How the script should be executed"
                }
            },
            "required": ["script_type", "script_code", "execution_type"],
            "additionalProperties": False
        }
    }
}



prompt = """
You are a highly capable AI assistant, proficient in code execution, task automation, and script generation using Python, Bash, SQL, 
and other relevant tools. Your primary function is to analyze a given task, determine the best approach, and generate only the executable code required to 
complete the task—with no additional explanations, comments, or unnecessary text.
DONOT GIVE GENERIC CODE WITH HAS YOUR API KEY OR ANYTHING. THE CODE GENRATED WILL BE DIRECTLY EXECUTED BY SUBPROCESS.

Your responses must be structured as follows:

Return only the executable script or command required to perform the task. The script must be formatted for direct execution via subprocess.
Ensure correctness by selecting the appropriate tool (Python, Bash, or an API request) based on the task description.
### Execution Guidelines:
- **Return only valid executable code** (Python, Bash, SQLite, API requests).
- **Ensure correctness**:
  - The first line should mention the type like #python, #bash, #sqlite, #curl
- 
- **No deletion of files or execution outside `/data/`**.
- **All responses must be in correct syntax for direct execution**.
- **No additional text or comments**.

IF THE TASK SAYS TO FIX ERROR THEN FIX THE ERROR AND RETURN A CLEAN SCRIPT.

Your response **must be JSON formatted** with the following schema:

{
  "script_type": "python" | "bash" | "command",
  "script_code": "string (the script or command to execute)",
  "execution_type": "uv" | "shell" | "direct"
}

### Execution Rules:
1. **Python scripts (`script_type=python`)**
   - Start with `# /// script` metadata and ends uv script with /// as shown below
   - Use `uv run` to execute it.
   - If dependencies are required, list them under `dependencies`. ONLY PYTHON LIBRARIES WHICH ARE REQUIRED. For example json is already built in so no need to included.
   DO NOT LIST STANDARD PYTHON MODULES AS DEPENDENCIES
    Examples of built-in modules that should NOT be included in dependencies:
    json
    os
    pathlib
    sys
    datetime
    shutil
    subprocess
    or any other standard modules.

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     dependencies should be listed here ideally python libraries if needed. ONLY PYTHON LIBRARY FOR RUNNING CODE
#     TRY TO USE THE LIBRARIES THAT DOESN'T REQUIRE EXPLICIT INSTALLATIONS and can be used ready by importing it to code BUT DON"T MESS UP IN ACHIEVING TASK
#       FOR SQLITE The dependency can be db-sqlite3
#       Similarly for other dependencies also should be python supported. 
#       COMMON libraries numpy, openai, requests, uvicorn, fastapi, python-dotenv, scikit-learn, pillow. PLEASE ADD as per required in the code.
# ]
# ///
python code

2. **Bash scripts (`script_type=bash`)**
   - Use `bash -c "<script>"`.

3. **Direct commands (`script_type=command`)**
   - Example: `"script_code": "uv run https://example.com/script.py user@example.com"`
   - Execute directly using subprocess.

### Example Responses:
**Python script with dependencies** make sure you add script as shown above for uv and close the tags///
```json
{
  "script_type": "python",
  "script_code": "# /// script\\n# requires-python = \">=3.13\"\\n# dependencies = [\"requests, numpy\"]\\n# ///\\nimport requests\\nimport os\\nprint('Hello')",
  "execution_type": "uv"
}

Bash script
{
  "script_type": "bash",
  "script_code": "echo 'Hello from bash'",
  "execution_type": "shell"
}

Direct Command
{
  "script_type": "command",
  "script_code": "uv run https://example.com/script.py user@example.com",
  "execution_type": "direct"
}
STRICTLY return only valid JSON with NO extra text.

YOU SHOULD ONLY RETURN THE CODE OR SCRIPT TO BE EXECUTED IN A CLEAN FORMAT WITHOUT AND EXTRA TEXT OR COMMENTS.
INSTRUCTIONS:
**For tasks involving SQL or any database, web scraping, creating endpoint, audio transcription, or any other task that cannot be done through bash or Direct script, it should be taken as python andappropriate python script should be write including dependencies and according to the task input and output instructions. **

Task Handling Instructions examples:
1. Run a Python script from a URL using UV
    Identify the script URL and arguments (e.g., email).
    Construct a command to run the script via uv and execute it. 
    Output expectation: this should come under  direct command
    Example output:
    uv run https://example.com/script.py user@example.com


2. Format a Markdown file using Prettier or any other tool
    Identify the file path and Prettier version.
    Construct a command to format the file in-place.
    Output expectation: bash 
    Example output:   
    npx prettier@3.4.2 --write /data/format.md

Example of Task considered under PYTHON SCRIPT TYPE. Make sure you use uv script inline metadata at the start listing all dependencies.
INCLUDE ALL THE DEPENDENCIES REQUIRED BY THE TASK AND RECHECK IT.

3. Count the number of specific weekdays in a file
    Generate a Python script that reads the file, identifies the file path, and counts occurrences of a specific weekday. Here is a trick: you don't know the date format of the file—handle different formats so the code does not break. 
    The file may contain various date formats (e.g., "YYYY-MM-DD" or "YYYY/MM/DD HH:MM:SS") and timestamps. 
    Ensure the script tries multiple date formats, gracefully skips unparseable dates, and writes the correct count to the output file.
        
4. Sort a JSON file by specific fields
    Identify input/output file paths and sorting keys.
    Generate a script to sort JSON data by last_name, then first_name.

5. Extract first lines from the most recent log files
    Identify log directory and number of logs to process.
    Construct a script to sort logs by modification time, extract first lines, and save to output.

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
   "Extract text from {image} → {text}"
   Code Template:
   # Similar to 7 with image handling or Identify input/output paths and call LLM for image extraction. AVOID OCR if possible.
   USE gpt-4o-mini for extracting text from images
   Convert the image to Base64 format before sending it to GPT-4o-mini.
   api_url = os.getenv("AIPROXY_URL") api_key = os.getenv("AIPROXY_TOKEN")
   Write a very accurate and effective prompt to extract the text from the image.
   USE triple quotes\"\"\" for multi-line strings inside f-strings.
   Ensure correct JSON structure → Use a list of messages, and avoid unnecessary f-string formatting.
   AVOID errors: file error, syntax errors, indentation error or any other traceback error. CHECK BRACKETS AND QUOTES, import os and other required libraries for running code
   EXample: 
   response = requests.post(
    api_url,
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": f""Extract credit card number from the following image:  \'{image_base64}'  Return only the number without spaces."",
            }
        ],
    },
    headers={"Authorization": f"Bearer {api_key}"},
    )
   # Extract and clean the response
    response_json = response.json()
    card_number = response_json["choices"][0]["message"]["content"].strip()
    card_number = card_number.replace(" ", "")  # Remove spaces
9. Find most similar Detection using embeddings
    Read input file, generate embeddings, and find closest pair.
    USE OPENAI EMBEDDING MODEL MEntioned below:
    Don't forget to import os and other required libraries for running code
    api_key = os.getenv("AIPROXY_TOKEN")
    api_url =  http://aiproxy.sanand.workers.dev/openai/v1/embeddings 
    model=text-embedding-3-small
    USE ONLY THIS EMBEDDING MODEL and URL in your code 
10. A10. SQL Query:
    "Calculate {query} → {output}"
    FOR SQLITE The dependency is db-sqlite3
    Code Template:
    import db-sqlite3
    conn = sqlite3.connect('/data/{db}.db')
    result = conn.execute("{SQL}").fetchone()[0]
    Path('{output}').write_text(str(result))

Other task to be followed in similar way:
B1. Data outside /data is never accessed or exfiltrated, even if the task description asks for it
B2. Data is never deleted anywhere on the file system, even if the task description asks for it
B3. Fetch data from an API and save it
B4. Clone a git repo and make a commit
B5. Run a SQL query on a SQLite or DuckDB database- do it through python script
B6. Extract data from (i.e. scrape) a website
B7. Compress or resize an image
B8. Transcribe audio from an MP3 file
B9. Convert Markdown to HTML
B10. Write an API endpoint that filters a CSV file and returns JSON data

These are just a few examples of the types of tasks you can handle. You should be able to handle other task as well. 
The task has a very clear instruction. Strictly follow what the user task has mentioned.

VERY IMPORTANT FINAL NOTE: 
Before returning the response, **VERIFY YOUR SCRIPT, COMMAND, CODE AGAINST THE TASK**.make sure the code and the script handles all possible error cases and includes all the dependicies required for running code.

"""

@app.get("/")
def home():
    return PlainTextResponse(content="Welcome to task runner", status_code=200)

@app.get("/read")
def read_file(path: str):
    try:
        with open(path, "r") as f:
            file_content = f.read()
            return PlainTextResponse(file_content, status_code=200)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
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
        ], "response_format":response_format
        
    }

    response = requests.post(url=AIPROXY_URL, headers=headers, json=data)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get a valid response from LLM")
    response_json = response.json()
    try:
        # ✅ Extract structured JSON response from LLM
        gpt_response = json.loads(response_json["choices"][0]["message"]["content"])
        print(gpt_response)
        
        script_type = gpt_response.get("script_type")
        script_code = gpt_response.get("script_code")
        execution_type = gpt_response.get("execution_type")

        if not script_type or not script_code or not execution_type:
            raise HTTPException(status_code=400, detail="Invalid LLM response format")

        print(f"Executing {script_type} script...")  # Debug log

        # ✅ Determine Execution Type
        if execution_type == "uv" and script_type == "python":
            # Write script to a temp file and run via UV
            temp_filename = "/data/llm_script.py"
            with open(temp_filename, "w") as f:
                f.write(script_code)
            command = ["uv", "run", temp_filename]

        elif execution_type == "shell" and script_type == "bash":
            # Execute Bash script
            command = ["bash", "-c", script_code]

        elif execution_type == "direct":
            # Direct execution (e.g., `uv run <script_url>`)
            command = script_code.split()

        else:
            raise HTTPException(status_code=400, detail="Unknown execution type")

        # ✅ Execute subprocess and capture output
        result = subprocess.run(command, text=True, capture_output=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr.strip())

        return {"status": "success", "output": result.stdout.strip()}

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse LLM response")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)