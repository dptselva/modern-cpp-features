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

    system_prompt = (
        "You are an expert AI C++ software engineer assistant.\n"
        "Your task is to fix the missing code element described in the user's issue inside the provided document.\n"
        "CRITICAL RULE: You must return the COMPLETELY rewritten document text content. Do not include any explanations, "
        "do not include introductory greetings, and do not wrap your output in ``` markdown backticks. Just output the text file content directly."
    )

    user_prompt = f"Target File Content:\n{original_content}\n\nIssue to Fix:\nTitle: {issue_title}\nBody: {issue_body}"

    print("Initializing Groq Client...")
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=api_key
    )

    # 🔥 PROACTIVE STEP: Programmatically discover a live model on Groq's active list
    print("Fetching active models list from Groq to find an online model...")
    try:
        models_list = client.models.list()
        active_models = [m.id for m in models_list.data]
        print(f"Available models found: {active_models}")
        
        # Prioritize any available text models (Llama 3.3, Qwen, or fallback GPT-OSS)
        selected_model = None
        for preference in ["llama-3.3", "llama3", "qwen3.6", "qwen", "gpt-oss", "llama"]:
            for model_id in active_models:
                if preference in model_id.lower() and "vision" not in model_id.lower() and "guard" not in model_id.lower():
                    selected_model = model_id
                    break
            if selected_model:
                break
                
        if not selected_model:
            # Absolute fallback to whatever the first text model is
            selected_model = active_models[0]
            
        print(f"✅ Proactively selected active model: {selected_model}")

    except Exception as e:
        print(f"⚠️ Could not fetch active models list dynamically: {e}. Falling back to default ID mapping.")
        selected_model = "llama-3.3-70b-versatile"

    print(f"Querying {selected_model} via Groq API...")
    try:
        completion = client.chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2
        )
        
        response_text = completion.choices[0].message.content

        if response_text.startswith("```"):
            response_text = "\n".join(response_text.splitlines()[1:])
        if response_text.endswith("```"):
            response_text = "\n".join(response_text.splitlines()[:-1])

        print(f"Writing automated corrections straight back into: {target_file}")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(response_text.strip())
        
        print("Agent actions completed successfully with zero file footprint changes!")

    except Exception as e:
        print(f"Failed to communicate with Groq API: {e}")
        exit(1)

if __name__ == "__main__":
    main()
