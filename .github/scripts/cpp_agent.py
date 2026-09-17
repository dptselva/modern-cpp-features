import os
import re
import requests

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY secret is not set.")
        exit(1)

    issue_title = os.getenv("ISSUE_TITLE", "")
    issue_body = os.getenv("ISSUE_BODY", "")

    target_file = "CPP23.md"
    if not os.path.exists(target_file):
        print(f"Error: Target file {target_file} not found.")
        exit(1)

    print(f"Reading target file: {target_file}")
    with open(target_file, 'r', encoding='utf-8') as f:
        original_content = f.read()

    system_prompt = (
        "You are an expert AI C++ software engineer assistant.\n"
        "Your task is to fix the missing code element described in the user's issue inside the provided document.\n"
        "CRITICAL RULE: You must return the COMPLETELY rewritten document text content. Do not include any explanations, "
        "do not include introductory greetings, and do not wrap your output in ``` markdown backticks. Just output the text file content directly."
    )

    user_prompt = f"Target File Content:\n{original_content}\n\nIssue to Fix:\nTitle: {issue_title}\nBody: {issue_body}"

    print("Querying openrouter/free router via direct HTTP request...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "GitHub Actions C++ Automation Agent"
    }
    
    payload = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post("https://openrouter.ai", headers=headers, json=payload)
    
    # Try to decode the json safely
    try:
        response_data = response.json()
    except Exception:
        print(f"❌ Failed to parse JSON. Raw API Server Response text was:\n{response.text}")
        exit(1)

    # Check if the API returned an explicit error block
    if "error" in response_data:
        print(f"❌ OpenRouter API returned an error: {response_data['error']}")
        exit(1)

    # Extract data safely without relying on object attributes
    if "choices" in response_data and len(response_data["choices"]) > 0:
        response_text = response_data["choices"][0]["message"]["content"]
    else:
        print(f"❌ Unexpected API structure. Full JSON data returned was:\n{response_data}")
        exit(1)

    # Sanitize accidental markdown framing backticks from the model if they are present
    if response_text.startswith("```"):
        response_text = "\n".join(response_text.splitlines()[1:])
    if response_text.endswith("```"):
        response_text = "\n".join(response_text.splitlines()[:-1])

    print(f"Writing automated corrections straight back into: {target_file}")
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(response_text.strip())
    
    print("Agent actions completed successfully with zero file footprint changes!")

if __name__ == "__main__":
    main()
