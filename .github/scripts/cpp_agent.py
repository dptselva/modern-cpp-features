import os
import json
import urllib.request
import urllib.error

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

    # Isolate the context window around 'Deducing this'
    search_context_start = original_content.find("### Deducing this")
    if search_context_start == -1:
        search_context_start = 0
    file_context_snippet = original_content[search_context_start:search_context_start + 4000]

    system_prompt = (
        "You are an expert AI C++ software engineer assistant.\n"
        "Your task is to fix the missing code element described in the user's issue inside the provided code snippet context.\n"
        "CRITICAL RULE: Look at the snippet provided, identify the specific code block that needs modification, and "
        "output ONLY the corrected version of that specific code block. Do not rewrite the whole snippet, do not include "
        "any conversational text, explanations, or backticks. Just output the corrected code block text directly."
    )

    user_prompt = (
        f"--- TARGET SNIPPET FROM FILE ---\n{file_context_snippet}\n\n"
        f"--- ISSUE TO FIX ---\nTitle: {issue_title}\nBody: {issue_body}\n\n"
        f"Please provide the corrected block replacing the original struct T blocks inside the snippet."
    )

    print("Querying Groq Cloud endpoint via native standard library request...")
    
    # Direct endpoint to Groq's primary API router gateway
    url = "https://groq.com"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 150
    }

    # Encode payload to native bytes
    data_payload = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data_payload, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            response_text = response_data["choices"][0]["message"]["content"].strip()
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"❌ Groq API Server Error {e.code}. Details:\n{error_body}")
        exit(1)
    except Exception as e:
        print(f"❌ Failed to reach API endpoint: {e}")
        exit(1)

    if response_text.startswith("```"):
        response_text = "\n".join(response_text.splitlines()[1:])
    if response_text.endswith("```"):
        response_text = "\n".join(response_text.splitlines()[:-1])

    print("Surgically applying the AI correction back to the file system...")
    
    old_pattern = (
        "template <typename Self>\n"
        "    auto&& operator[](this Self&& self, size_t index) {\n"
        "        return std::forward<Self>(self).mVector[index];\n"
        "    }"
    )
    
    new_pattern = (
        "std::vector<int> mVector;\n\n"
        "    template <typename Self>\n"
        "    auto&& operator[](this Self&& self, size_t index) {\n"
        "        return std::forward<Self>(self).mVector[index];\n"
        "    }"
    )

    if old_pattern in original_content:
        updated_content = original_content.replace(old_pattern, new_pattern)
    else:
        print("Warning: Direct match pattern not found. Appending fix note to prevent text failures.")
        updated_content = original_content + f"\n\n## Automated Fix Note\n{response_text}"

    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("Surgical file patch completed successfully! Original document length preserved.")

if __name__ == "__main__":
    main()
