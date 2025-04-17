import asyncio
import json
import re
import difflib
from openai import OpenAI
from playwright.async_api import async_playwright

client = OpenAI(api_key="")  # replace with your actual key
#TARGET_URL = "https://docs.google.com/forms/d/1uMkzOGtiVN_VqtPPjTInpd1nP64Ii_3vdMaNlwU6Z8Y/viewform"

TARGET_URL = "https://www.jotform.com/build/251057968491165"

async def extract_and_prepare_for_gpt(page):
    elements = await page.query_selector_all("input, textarea, select")
    questions = []
    for el in elements:
        try:
            tag = await el.evaluate("e => e.tagName.toLowerCase()")
            el_type = await el.get_attribute("type") or "text"
            qtype = "text"
            options = []
            label = await el.get_attribute("placeholder") or await el.get_attribute("aria-label")
            if not label:
                el_id = await el.get_attribute("id")
                if el_id:
                    label_el = await page.query_selector(f"label[for='{el_id}']")
                    if label_el:
                        label = await label_el.inner_text()
            if not label:
                label_handle = await el.evaluate_handle("""
                    (e) => {
                        let current = e;
                        while (current && current.parentElement) {
                            current = current.parentElement;
                            const label = current.querySelector('label, span, div');
                            if (label && label.innerText && label.innerText.length < 100) {
                                return label;
                            }
                        }
                        return null;
                    }
                """)
                if label_handle:
                    label = await label_handle.evaluate("e => e.innerText")
            label = label.strip() if label else "[Unknown Question]"
            if tag == "textarea":
                qtype = "textarea"
            elif tag == "select":
                qtype = "select"
                option_elements = await el.query_selector_all("option")
                options = [await opt.inner_text() for opt in option_elements if await opt.inner_text()]
            elif el_type in ["radio", "checkbox"]:
                qtype = el_type
                wrapper = await el.evaluate_handle("e => e.closest('div')")
                label_elements = await wrapper.query_selector_all("label") if wrapper else []
                for lbl in label_elements:
                    try:
                        text = await lbl.inner_text()
                        if text and len(text.strip()) > 2 and text.strip() not in options:
                            options.append(text.strip())
                    except:
                        continue
            if el_type != "submit":
                questions.append({
                    "question": label,
                    "type": qtype,
                    "options": options
                })
        except Exception as e:
            print(f"⚠️ Extraction error: {e}")
            continue
    for q in questions:
        if q["type"] in ["radio", "checkbox", "select"] and not q["options"]:
            print(f"⚠️ Downgrading malformed {q['type']} to text: {q['question']}")
            q["type"] = "text"
    return questions

def build_prompt_from_structured(questions):
    prompt = """You are a JSON-only agent.

Return only a valid JSON array of question-answer objects with no explanation or markdown.

Each item must include:
- "question": string
- "type": one of ["text", "textarea", "checkbox", "radio", "select"]
- "options": list of strings (empty if not applicable)
- "answer": realistic example answer (must match one or more listed options exactly for choice-based types)

Here is the list of questions:
"""
    for q in questions:
        prompt += f'- Question: "{q["question"]}", Type: "{q["type"]}", Options: {q["options"]}\n'
    return prompt

def extract_json_block(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)
    return match.group(0).strip() if match else None

def extract_questions_with_answers_from_structured(questions):
    prompt = build_prompt_from_structured(questions)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    content = response.choices[0].message.content.strip()
    print("\n🧠 Raw GPT Output:\n", content)
    return extract_json_block(content)

async def get_html_and_fill_form(url, responses):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(3000)
        for item in responses:
            try:
                question = item.get("question", "").lower()
                answer = item.get("answer", "")
                qtype = item.get("type", "text")
                options = item.get("options", [])
                normalized = normalize_answer(answer, options, is_multi=(qtype == "checkbox"))
                if qtype in ["text", "textarea"]:
                    inputs = await page.query_selector_all("input, textarea")
                    for el in inputs:
                        placeholder = await el.get_attribute("placeholder") or ""
                        aria_label = await el.get_attribute("aria-label") or ""
                        if question in placeholder.lower() or question in aria_label.lower():
                            await el.fill(answer)
                            break
                elif qtype == "radio":
                    radios = await page.query_selector_all('input[type="radio"]')
                    for radio in radios:
                        label = await radio.get_attribute("aria-label") or ""
                        if normalized and normalized[0].lower() in label.lower():
                            await radio.click()
                            break
                elif qtype == "checkbox":
                    checkboxes = await page.query_selector_all('input[type="checkbox"]')
                    for cb in checkboxes:
                        label = await cb.get_attribute("aria-label") or ""
                        for sel in normalized:
                            if sel.lower() in label.lower():
                                await cb.click()
                                break
                elif qtype == "select":
                    selects = await page.query_selector_all("select")
                    for select in selects:
                        if normalized:
                            await select.select_option(label=normalized[0])
                            break
            except Exception as e:
                print(f"⚠️ Failed to fill {item.get('question')}: {e}")
        print("✅ Form auto-filled.")
        await page.wait_for_timeout(5000)
        await browser.close()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TARGET_URL)
        await page.wait_for_timeout(3000)
        questions = await extract_and_prepare_for_gpt(page)
        await browser.close()

    json_str = extract_questions_with_answers_from_structured(questions)
    if not json_str:
        print("❌ GPT did not return a valid JSON array.")
        return

    try:
        answers = json.loads(json_str)
    except Exception as e:
        print("❌ Failed to parse GPT output:", e)
        return

    with open("extracted_questions.json", "w") as f:
        json.dump(answers, f, indent=2)
        print("📁 Saved extracted questions to extracted_questions.json")

    await get_html_and_fill_form(TARGET_URL, answers)

if __name__ == "__main__":
    asyncio.run(main())
