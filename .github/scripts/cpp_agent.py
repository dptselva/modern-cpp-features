import os

def main():
    target_file = "CPP23.md"
    if not os.path.exists(target_file):
        print(f"Error: Target file {target_file} not found.")
        exit(1)

    with open(target_file, 'r', encoding='utf-8') as f:
        original_content = f.read()

    old_new_way = "struct T {\n  decltype(auto) operator[](this auto& self, std::size_t idx) {\n    return self.mVector[idx];\n  }\n};"
    fixed_new_way = "struct T {\n  std::vector<int> mVector;\n\n  decltype(auto) operator[](this auto& self, std::size_t idx) {\n    return self.mVector[idx];\n  }\n};"
    
    old_old_way = "struct T {\n  value_t& operator[](std::size_t idx) { return mVector[idx]; }\n  const value_t& operator[](std::size_t idx) const { return mVector[idx]; }\n};"
    fixed_old_way = "struct T {\n  std::vector<int> mVector;\n\n  value_t& operator[](std::size_t idx) { return mVector[idx]; }\n  const value_t& operator[](std::size_t idx) const { return mVector[idx]; }\n};"

    if "std::vector<int> mVector;" in original_content:
        print("Target pattern already updated. Skipping file edits.")
    elif old_new_way in original_content or old_old_way in original_content:
        updated_content = original_content.replace(old_new_way, fixed_new_way).replace(old_old_way, fixed_old_way)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    else:
        import re
        updated_content = re.sub(r"(struct\s+T\s*\{)", r"\1\n  std::vector<int> mVector;", original_content)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)

if __name__ == "__main__":
    main()
