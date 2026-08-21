import os

def main():
    search_dir = "d:\\Code\\vibedm\\backend\\app"
    keyword = "active"
    print(f"Searching for '{keyword}' in {search_dir}...")
    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if keyword in line and ("workspace" in line or "select" in line or "insert" in line):
                                print(f"{path}:{line_num}: {line.strip()}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    main()
