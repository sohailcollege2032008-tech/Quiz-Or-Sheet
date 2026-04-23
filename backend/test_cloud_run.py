import httpx
import os
import json
import asyncio

def generate_standalone_quiz(questions, file_name):
    questions_json = json.dumps(questions, indent=4, ensure_ascii=False)
    quiz_title = os.path.splitext(file_name)[0] + " - Quiz"
    html_template = f"""<!DOCTYPE html>
<html lang="ar" dir="auto">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{quiz_title}</title>
    <style>
        :root {{ --primary: #2c3e50; --secondary: #34495e; --success: #27ae60; --danger: #e74c3c; --light: #f4f7f6; }}
        body {{ font-family: 'Segoe UI', sans-serif; background: var(--light); padding: 20px; display: flex; justify-content: center; }}
        .quiz-container {{ background: white; width: 100%; max-width: 850px; padding: 25px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: var(--primary); border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        .question-box {{ margin-bottom: 20px; padding: 15px; border-bottom: 1px solid #eee; }}
        .options {{ margin-top: 10px; }}
        .correct {{ color: var(--success); font-weight: bold; }}
    </style>
</head>
<body>
<div class="quiz-container">
    <h1>{quiz_title}</h1>
    <div id="questions">
        {"".join([f'<div class="question-box"><h3>Q{i+1}: {q["q"]}</h3><ul>' + "".join([f'<li class="{"correct" if j==q["c"] else ""}">{"✅ " if j==q["c"] else ""}{opt}</li>' for j, opt in enumerate(q["a"])]) + '</ul></div>' for i, q in enumerate(questions)])}
    </div>
</div>
</body>
</html>"""
    return html_template

async def run_cloud_test():
    url = "https://quiz-backend-776350978260.us-central1.run.app/process"
    pdf_path = r"C:\Users\ASUS\Downloads\Telegram Desktop\60 end module - Teacher Version (Answered).pdf"
    
    print(f"Testing Cloud Run API: {url}")
    print(f"File: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print("File not found!")
        return

    files = {'file': (os.path.basename(pdf_path), open(pdf_path, 'rb'), 'application/pdf')}
    
    questions = []
    
    async with httpx.AsyncClient(timeout=1800) as client:
        async with client.stream("POST", url, files=files) as response:
            print(f"Status Code: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    # Try to see if it's a log or a result
                    if data.startswith("[") and data.endswith("]"):
                        # Likely the final JSON result
                        try:
                            questions = json.loads(data)
                            print(f"\n[RESULT] Received {len(questions)} questions.")
                        except:
                            pass
                    else:
                        print(f"[LOG] {data}")

    if questions:
        # Save JSON
        with open("cloud_result.json", "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print("JSON saved to cloud_result.json")
        
        # Save HTML
        html_content = generate_standalone_quiz(questions, os.path.basename(pdf_path))
        with open("cloud_quiz.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("HTML saved to cloud_quiz.html")
    else:
        print("No questions extracted.")

if __name__ == "__main__":
    asyncio.run(run_cloud_test())
