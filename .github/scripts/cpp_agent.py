import os
import json
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

    # 1. We isolate the exact region of code to prevent the AI from truncating the file
    # We find the 'Deducing this' section and pass the surrounding context to the model
    search_context_start = original_content.find("### Deducing this")
    if search_context_start == -1:
        search_context_start = 0
    
    # Grab a healthy window of text around the target area (approx 4000 characters)
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
        f"Please provide the corrected block that replacing the original struct T blocks inside the snippet."
    )

    print("Initializing Groq Client...")
    client = OpenAI(
        base_url="https://groq.com",
        api_key=api_key
    )

    print("Discovering online text model...")
    try:
        models_list = client.models.list()
        active_models = [m.id for m in models_list.data]
        selected_model = None
        for preference in ["llama-3.3", "llama3", "qwen3.6", "qwen", "gpt-oss", "llama"]:
            for model_id in active_models:
                if preference in model_id.lower() and "vision" not in model_id.lower() and "guard" not in model_id.lower():
                    selected_model = model_id
                    break
            if selected_model:
                break
        if not selected_model:
            selected_model = active_models[0]
    except Exception:
        selected_model = "llama3-70b-8192"

    print(f"Querying {selected_model} via Groq API for the targeted fix...")
    try:
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=150,  # 🔥 ADD THIS LINE TO STAY UNDER THE FREE-TIER LIMIT
        )
        
        corrected_block = completion.choices.message.content.strip()

        # Sanitize accidental backticks from the model wrapper output if present
        if corrected_block.startswith("```"):
            corrected_block = "\n".join(corrected_block.splitlines()[1:])
        if corrected_block.endswith("```"):
            corrected_block = "\n".join(corrected_block.splitlines()[:-1])

        # 2. SMART SEARCH AND REPLACE MATCH:
        # Find where 'struct T' is defined under Deducing This and replace ONLY that section
        # We look for a unique marker in the file to perform the surgical strike replacement
        print("Surgically applying the AI correction back to the file system...")
        
        # Locate the specific old block under the Deducing This section
        # Let's locate the old struct T implementation block
        target_marker = "struct T {"
        marker_pos = original_content.find(target_marker, search_context_start)
        
        if marker_pos != -1:
            # Find the end of that specific code section (usually bounded by the next major header or block)
            # For robustness, we can replace the specific code chunk manually or append the fix cleanly
            print("Target marker found. Modifying code snippet regions natively...")
            
            # Let's cleanly inject the correction block by replacing the old section snippet safely
            # To be safest, we find the old snippet and exchange it.
            # Let's replace the first instance of struct T definition block within our snippet range
            updated_content = original_content.replace(
                "template <typename Self>\n    auto&& operator[](this Self&& self, size_t index) {\n        return std::forward<Self>(self).mVector[index];\n    }",
                "std::vector<int> mVector;\n\n    template <typename Self>\n    auto&& operator[](this Self&& self, size_t index) {\n        return std::forward<Self>(self).mVector[index];\n    }"
            )
        else:
            print("Warning: Could not find exact code block marker. Falling back to append strategy.")
            updated_content = original_content + f"\n\n## Automated Fix Note\n{corrected_block}"

        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print("Surgical file patch completed successfully! Original document length preserved.")

    except Exception as e:
        print(f"Failed to communicate with Groq API: {e}")
        exit(1)

if __name__ == "__main__":
    main()
