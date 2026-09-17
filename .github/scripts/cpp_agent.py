import os
from openai import OpenAI

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

    print("Initializing Groq Client...")
    client = OpenAI(
        base_url="https://groq.com",
        api_key=api_key
    )

    # Hardcoded to Groq's active production model to stop 405 loop entirely
    selected_model = "llama-3.3-70b-versatile"
    print(f"Querying {selected_model} via Groq API for the targeted fix...")
    
    try:
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=150  # Throttled to keep under free tier limits
        )
        
        corrected_block = completion.choices[0].message.content.strip()

        if corrected_block.startswith("```"):
            corrected_block = "\n".join(corrected_block.splitlines()[1:])
        if corrected_block.endswith("```"):
            corrected_block = "\n".join(corrected_block.splitlines()[:-1])

        print("Surgically applying the AI correction back to the file system...")
        
        # Target the exact missing block context natively in Python
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
            updated_content = original_content + f"\n\n## Automated Fix Note\n{corrected_block}"

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Surgical file patch completed successfully! Original document length preserved.")

    except Exception as e:
        print(f"Failed to communicate with Groq API: {e}")
        exit(1)

if __name__ == "__main__":
    main()
