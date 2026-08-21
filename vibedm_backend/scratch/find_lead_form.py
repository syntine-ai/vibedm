file_path = r"d:\Code\vibedm\vibedm_frontend\src\routes\automations.$id.edit.tsx"
with open(file_path, encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "function AskFollowResponseEditor" in line or "const AskFollowResponseEditor" in line:
        print(f"Line {i+1}: {line.strip()}")
        for j in range(i+1, min(i+80, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")

    if "function LeadFormResponseEditor" in line or "const LeadFormResponseEditor" in line:
        print(f"Line {i+1}: {line.strip()}")
        for j in range(i+1, min(i+80, len(lines))):
            print(f"  {j+1}: {lines[j].strip()}")
