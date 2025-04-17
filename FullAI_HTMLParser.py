import asyncio
import json
import re
from openai import OpenAI
from playwright.async_api import async_playwright

client = OpenAI(api_key="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")
TARGET_URL = "https://www.jotform.com/build/251060439239152?s=templates"


def extract_json_block(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    return match.group(0).strip() if match else None


async def parse_form_html_via_gpt(text):
    example = '''
[
  {
    "question": "Your name",
    "type": "text",
    "options": [],
    "answer": "Alice Smith"
  },
  {
    "question": "Gender",
    "type": "radio",
    "options": ["Male", "Female", "Other"],
    "answer": "Female"
  }
]
'''

    prompt = f"""
You are a smart form-parsing assistant.
Given the raw HTML of a webpage that contains a form, return a JSON array of question-answer items.

Each object must include:
- \"question\": string
- \"type\": one of [\"text\", \"textarea\", \"checkbox\", \"radio\", \"select\"]
- \"options\": list of strings (if applicable, otherwise empty)
- \"answer\": a realistic, sensible answer for testing

Return only a valid JSON array. No explanation, no markdown.

Example output:
{example}

TEXT:
{text[:90000]}
"""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    content = response.choices[0].message.content.strip()
    print("\n🧠 Raw GPT Output:\n", content)
    json_str = extract_json_block(content)
    try:
        return json.loads(json_str)
    except Exception as e:
        print("❌ Failed to parse GPT output:", e)
        return []


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TARGET_URL)
        await page.wait_for_timeout(3000)
        visible_text = await page.inner_text("body")
        await browser.close()

        print("📁 Saved extracted answers to extracted_answers_from_html.json")

    answers = await parse_form_html_via_gpt(visible_text)

    if not isinstance(answers, list):
        print("❌ Unexpected GPT output format. Skipping save.")
        return

    with open("extracted_answers_from_html.json", "w") as f:
        json.dump(answers, f, indent=2)
        print("\n📁 Saved extracted questions and answers to extracted_answers_from_html.json")


if __name__ == "__main__":
    asyncio.run(main())
