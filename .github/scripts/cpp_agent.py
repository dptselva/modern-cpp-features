import os
from openai import OpenAI

def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY secret is not set.")
        exit(1)

    issue_title = os.getenv("ISSUE_TITLE", "")
    issue_body = os.getenv("ISSUE_BODY", "")

    print("Initializing OpenRouter Client...")
    client = OpenAI(
        base_url="https://openrouter.ai",
        api_key=api_key,
    )

    # Hard-targeted file path to completely stop file generation errors
    target_file = "CPP23.md"
    
    if not os.path.exists(target_file):
        print(f"Error: Target file {target_file} not found at repository root.")
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

    print("Querying openrouter/free router...")
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com", 
                "X-Title": "GitHub Actions C++ Automation Agent",
            },
            model="openrouter/free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Pull response safely out of the options array
        response_text = completion.choices[0].message.content
        
        # Secondary fallback clean to sanitize accidental markdown framing backticks from the model
        if response_text.startswith("```"):
            # Strip first line if it contains the markdown header string
            response_text = "\n".join(response_text.splitlines()[1:])
        if response_text.endswith("```"):
            response_text = "\n".join(response_text.splitlines()[:-1])

        print(f"Writing automated corrections straight back into: {target_file}")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(response_text.strip())
        
        print("Agent actions completed successfully with zero file footprint changes!")

    except Exception as e:
        print(f"Failed to communicate with OpenRouter API: {e}")
        exit(1)

if __name__ == "__main__":
    main()
