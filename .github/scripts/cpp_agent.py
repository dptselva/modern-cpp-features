import os
import json
import urllib.request

def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY secret is not set.")
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

    print("Querying Groq Cloud endpoint via native HTTP client...")
    
    url = "https://groq.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        # 🔥 FIX: Swapped to Groq's most stable production model path
        "model": "llama3-70b-8192", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2
    }

    # Ensure json data payloads are wrapped cleanly
    data_payload = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_payload, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            response_text = response_data["choices"][0]["message"]["content"]
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Groq API Server Error {e.code}. Details:\n{error_body}")
        exit(1)
    except Exception as e:
        print(f"❌ Failed to reach API endpoint: {e}")
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
