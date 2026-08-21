import os

def main():
    search_dir = "d:\\Code\\vibedm\\backend"
    keyword = "syntine.com"
    print(f"Searching for '{keyword}' in {search_dir}...")
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith((".py", ".env", ".example", ".toml")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if keyword in line:
                                print(f"{path}:{line_num}: {line.strip()}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    main()
