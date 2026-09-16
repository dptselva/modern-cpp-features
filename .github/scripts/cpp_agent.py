import os
import re
from openai import OpenAI

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY secret is not set.")
        exit(1)

    issue_title = os.getenv("ISSUE_TITLE", "")
    issue_body = os.getenv("ISSUE_BODY", "")
    issue_context = f"Title: {issue_title}\n\nBody:\n{issue_body}".lower()

    print("Initializing OpenRouter Client...")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    relevant_extensions = ('.cpp', '.hpp', '.h', '.cc', '.md')
    code_base_context = ""
    target_files_found = []

    print("Scanning repository for relevant files...")
    for root, dirs, files in os.walk("."):
        if '.git' in root or '.github' in root:
            continue
        for file in files:
            if file.endswith(relevant_extensions):
                file_path = os.path.join(root, file)
                file_name_lower = file.lower()
                
                if "cpp23" in issue_context and "cpp23" not in file_name_lower:
                    continue 

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        code_base_context += f"\n--- FILE: {file_path} ---\n{content}\n"
                        target_files_found.append(file_path)
                except Exception as e:
                    print(f"Skipping file {file_path} due to error: {e}")

    print(f"Bundled {len(target_files_found)} files into context.")

    system_prompt = (
        "You are an expert AI C++ software engineer agent. Your task is to resolve the user's issue "
        "by modifying the repository files provided in the context. "
        "CRITICAL INSTRUCTION: You must respond ONLY with the fully rewritten file content wrapped in a markdown code block. "
        "Identify which file needs to be modified, rewrite its content entirely with the requested fix, "
        "and start your response with '```' followed by the file path. Do not explain your changes."
    )

    user_prompt = f"Here is the repository context:\n{code_base_context}\n\nHere is the issue to fix:\n{issue_title}\n{issue_body}"

    # 🚨 DYNAMIC FIX: Forcing Llama-3.3-70b-instruct:free explicitly
    selected_model = "meta-llama/llama-3.3-70b-instruct:free"
    print(f"Querying {selected_model} via OpenRouter...")
    
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com", 
                "X-Title": "GitHub Actions C++ Automation Agent",
            },
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Safe Response Safeguard: check if completion is a string (OpenRouter error message)
        if isinstance(completion, str):
            print(f"❌ Error: OpenRouter returned an invalid response block string instead of an object: {completion}")
            exit(1)
            
        if not hasattr(completion, 'choices') or not completion.choices:
            print(f"❌ Error: Response object does not have choices. Raw Response: {completion}")
            exit(1)
            
        response_text = completion.choices[0].message.content
        print("AI successfully responded. Processing changes...")

        pattern = r"```(?:\.\/)?([a-zA-Z0-9_\-\.\/]+)\n(.*?)```"
        matches = re.findall(pattern, response_text, re.DOTALL)

        if not matches:
            print("Error: Could not parse file changes from AI response.")
            print(f"Raw Response: {response_text}")
            exit(1)

        for file_path, new_content in matches:
            file_path = file_path.strip()
            print(f"Writing automated modifications back to: {file_path}")
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content.strip())
        
        print("Agent actions completed successfully!")

    except Exception as e:
        print(f"Failed to communicate with OpenRouter API: {e}")
        exit(1)

if __name__ == "__main__":
    main()
