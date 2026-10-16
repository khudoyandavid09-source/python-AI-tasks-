import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request

REPO_PATH = "."
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1"


def generate_readme_locally(file_name, code_content):
  prompt = f"Analyze this Python script ({file_name}). Write a clean README.md in English with description, explanation, and run instructions.\n\n```python\n{code_content}\n```\n\nReturn ONLY markdown starting with the title."
  payload = {
      "model": MODEL_NAME,
      "prompt": prompt,
      "stream": False,
      "options": {"temperature": 0.3},
  }
  data = json.dumps(payload).encode("utf-8")
  req = urllib.request.Request(
      OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}
  )
  try:
    with urllib.request.urlopen(req, timeout=120) as response:
      res = json.loads(response.read().decode("utf-8"))
      return res.get("response", f"# Task {file_name}")
  except urllib.error.URLError as e:
    print(f"Ollama error: {e}")
    return None


def run_git_command(args):
  res = subprocess.run(
      ["git"] + args, cwd=REPO_PATH, text=True, capture_output=True
  )
  if res.returncode != 0:
    print(f"Git warning/error: {res.stderr.strip()}")
    return False
  return True


def run_pipeline():
  py_files = [
      f
      for f in os.listdir(REPO_PATH)
      if f.endswith(".py") and f != "auto_pipeline.py"
  ]
  if not py_files:
    print("No .py files found to process.")
    return

  processed_paths = []

  for py_file in sorted(py_files):
    file_path = os.path.join(REPO_PATH, py_file)
    with open(file_path, "r", encoding="utf-8") as f:
      code = f.read()

    print(f"🤖 Generating README for {py_file}...")
    readme = generate_readme_locally(py_file, code)
    if not readme:
      continue

    base_name = os.path.splitext(py_file)[0]
    task_dir = os.path.join(REPO_PATH, f"task_{base_name}")
    os.makedirs(task_dir, exist_ok=True)

    new_py_path = os.path.join(task_dir, py_file)
    if os.path.abspath(file_path) != os.path.abspath(new_py_path):
      shutil.move(file_path, new_py_path)

    readme_path = os.path.join(task_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as rf:
      rf.write(readme)

    print(f"📁 Organized: task_{base_name}/")
    processed_paths.extend([new_py_path, readme_path])

  if processed_paths:
    print("🚀 Staging and pushing to GitHub...")
    for path in processed_paths:
      run_git_command(["add", path])

    if run_git_command(
        ["commit", "-m", "Auto-generated solutions and AI READMEs"]
    ):
      if run_git_command(["push", "origin", "main"]):
        print("✅ Successfully pushed to GitHub!")
      else:
        print("⚠️ Push failed. Check your git remote and branch.")


if __name__ == "__main__":
  run_pipeline()
