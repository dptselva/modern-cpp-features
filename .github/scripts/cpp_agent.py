import os
import json
import glob
from openai import OpenAI

def find_cpp_files():
    # Recursively find all C++ source and header files in the repo
    files = []
    for ext in ['*.cpp', '*.hpp', '*.h', '*.cc', '*.cxx','*.md']:
        files.extend(glob.glob(f'**/{ext}', recursive=True))
    return [f for f in files if 'node_modules' not in f and '.git' not in f]

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    issue_title = os.getenv("ISSUE_TITLE", "")
    issue_body = os.getenv("ISSUE_BODY", "")
    
    if not api_key:
        print("Error: OPENROUTER_API_KEY secret is not set.")
        return

    print("Scanning repository for C++ files...")
    cpp_files = find_cpp_files()
    if not cpp_files:
        print("No C++ files found in the workspace.")
        return
        
    print(f"Found files: {cpp_files}")

    # Build context by listing the files and their content summary for the LLM
    repo_context = ""
    for filepath in cpp_files[:10]: # Limit to first 10 files for context safety
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            repo_context += f"\n--- FILE: {filepath} ---\n{content}\n"
        except Exception as e:
            print(f"Could not read {filepath}: {e}")

    # Connect to OpenRouter using OpenAI SDK compatibility
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    system_prompt = (
        "You are an expert C++ Senior Software Engineer AI agent.\n"
        "Your task is to analyze a GitHub issue along with the repository files, "
        "and determine exactly which file needs a change and what that change should be.\n"
        "You must respond ONLY with a JSON object matching this structure:\n"
        "{\n"
        "  \"file_path\": \"path/to/file.cpp\",\n"
        "  \"new_content\": \"the entire complete updated text of the file\"\n"
        "}\n"
        "Do not include any explanation, markdown blocks, or extra text outside the JSON."
    )

    user_prompt = f"ISSUE TITLE: {issue_title}\nISSUE DESCRIPTION:\n{issue_body}\n\nREPOSITORY SOURCE FILES:\n{repo_context}"

    print("Querying Qwen 2.5 Coder via OpenRouter...")
    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "role", "content": user_prompt} if hasattr(OpenAI, "deprecated") else {"role": "user", "content": user_prompt}
        ],
        temperature=0.1
    )

    raw_output = response.choices[0].message.content.strip()
    
    # Strip markdown block formatting if the LLM ignores instructions and adds it
    if raw_output.startswith("```"):
        raw_output = raw_output.strip("`").replace("json", "", 1).strip()

    try:
        result = json.loads(raw_output)
        target_file = result.get("file_path")
        new_content = result.get("new_content")

        if target_file and new_content:
            print(f"Applying AI changes to {target_file}...")
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("Changes successfully applied to workspace.")
        else:
            print("AI response was malformed or missing keys.")
    except Exception as e:
        print(f"Failed to parse AI response as JSON: {e}")
        print(f"Raw Output was:\n{raw_output}")

if __name__ == "__main__":
    main()