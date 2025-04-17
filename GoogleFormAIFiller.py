import time
import openai
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from openai import OpenAI

# === CONFIG ===
CHROMEDRIVER_PATH = "chromedriver-mac-x64/chromedriver"  # ✅ Update this path
client = OpenAI(api_key="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")


# === ROBUST QUESTION TEXT EXTRACTOR ===
def extract_question_text(question):
    try:
        # Try standard title container
        primary = question.find_elements(By.CSS_SELECTOR, 'div.freebirdFormviewerComponentsQuestionBaseTitle')
        if primary and primary[0].text.strip():
            return primary[0].text.strip()

        # Fallback: grab first meaningful span
        span_texts = [
            span.text.strip()
            for span in question.find_elements(By.CSS_SELECTOR, 'span')
            if span.text.strip()
        ]
        for text in span_texts:
            if len(text) > 5 and not text.startswith("("):  # ignore help text like (optional)
                return text
    except Exception as e:
        print(f"[ERROR] Extracting question text: {e}")
    return "[Unknown Question]"


# === GPT TEXT ANSWER HANDLER ===
def generate_ai_answer_for_text(question_text):
    messages = [
        {"role": "system", "content": "You are a helpful assistant answering form questions concisely."},
        {"role": "user", "content": f"Q: {question_text}\nA:"}
    ]
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Text answer: {e}")
        return "N/A"



# === GPT MULTIPLE CHOICE/ CHECKBOX HANDLER ===
# === GPT MULTIPLE CHOICE/ CHECKBOX HANDLER ===
def generate_ai_answer_for_choices(question_text, choices, multi_select=False, retries=2):
    if not any(choices):
        return "0"

    examples = (
        "Q: Which apply to secure behavior?\n"
        "Choices:\n1. Use a strong password\n2. Lock your screen\n3. Share credentials\n4. Use 2FA\n5. Reuse passwords\n"
        "Select multiple. A: 1,2,4\n\n"
        "Q: What is 2 + 2?\n"
        "Choices:\n1. 3\n2. 4\n3. 5\nSelect one. A: 2\n"
    )

    instructions = (
        "You are completing a security awareness training assessment. "
        "Each question is part of a workplace cybersecurity quiz.\n"
        "Always select answers based only on the numbered choices provided.\n"
        "If multiple apply, return comma-separated numbers like '1,3'. "
        "If only one is correct, return a single number. Do not explain your reasoning."
    )

    choices_prompt = "\n".join(f"{i+1}. {c}" for i, c in enumerate(choices))
    final_note = (
        "Select all that apply. Respond only with numbers like '1,3'."
        if multi_select else
        "Select only one. Respond with a single number like '2'."
    )

    prompt = f"{instructions}\n\n{examples}Q: {question_text}\nChoices:\n{choices_prompt}\n{final_note}\nA:"

    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=100
            )
            answer = response.choices[0].message.content.strip()
            print(f"[GPT Choice Answer Raw] {answer}")
            if any(char.isdigit() for char in answer):
                return answer
        except Exception as e:
            print(f"[ERROR] GPT (attempt {attempt + 1}) failed: {e}")

    return "0"



# === PARSE CHOICE INDEX FROM GPT OUTPUT ===
def parse_choices_indices(answer_text, max_index, multi_select=False):
    try:
        answer_text = (
            answer_text.lower()
            .replace("option", "")
            .replace("answer", "")
            .replace("and", ",")
            .replace(";", ",")
        )
        parts = answer_text.split(',')
        indices = [int(p.strip()) - 1 for p in parts if p.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < max_index]
        return list(set(indices)) if multi_select else ([indices[0]] if indices else [])
    except Exception as e:
        print(f"[ERROR] Parsing indices: {e}")
        return []


# === EXTRACT LABELS FROM OPTIONS ===
def extract_choices(elements):
    choices_text = []
    for el in elements:
        try:
            label = el.get_attribute("aria-label")
            if label:
                choices_text.append(label.strip())
            else:
                spans = el.find_elements(By.CSS_SELECTOR, 'span')
                text = " ".join(span.text.strip() for span in spans if span.text.strip())
                choices_text.append(text or "<empty>")
        except Exception:
            choices_text.append("<error>")
    return choices_text


# === MAIN SCRIPT ===

def main():
    FORM_URL = "https://docs.google.com/forms/d/1uMkzOGtiVN_VqtPPjTInpd1nP64Ii_3vdMaNlwU6Z8Y/viewform"
    service = Service(executable_path=CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    actions = ActionChains(driver)

    try:
        driver.get(FORM_URL)
        time.sleep(4)

        question_containers = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        print(f"\n🔎 Found {len(question_containers)} questions.")

        for q_index, question in enumerate(question_containers, start=1):
            try:
                question_text = extract_question_text(question)

                if question_text == "[Unknown Question]":
                    print(f"⚠️ Missing label — using fallback for question {q_index}")
                    question_text = f"Question {q_index}"

                if not re.match(r"^\d+\.\s", question_text):
                    print(f"⏭️ Skipping: Not numbered → {question_text}")
                    continue

                # === EMAIL ===
                if "email" in question_text.lower():
                    email_field = question.find_element(By.CSS_SELECTOR, 'input[type="email"], input[type="text"]')
                    email_field.send_keys("bshetty@oncentrl.com")
                    continue

                # === TEXT FIELD ===
                text_inputs = question.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea')
                if text_inputs:
                    answer = generate_ai_answer_for_text(question_text)
                    print(f"→ Text Answer: {answer}")
                    text_inputs[0].send_keys(answer)
                    continue

                # === RADIO ===
                radios = question.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                if radios:
                    choices_text = extract_choices(radios)
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=False)
                    print(f"[GPT Raw Answer] {ai_answer}")
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text))
                    if selected_indices:
                        expected_text = choices_text[selected_indices[0]].lower().strip()
                        for radio in radios:
                            label = radio.get_attribute("aria-label") or ""
                            if expected_text in label.lower():
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio)
                                driver.execute_script("arguments[0].click();", radio)
                                print(f"✓ Selected: {expected_text}")
                                break
                    else:
                        print("⚠️ GPT was unsure — radio skipped.")
                    continue

                # === CHECKBOXES ===
                checkboxes = question.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                if checkboxes:
                    # Map checkbox aria-labels
                    label_map = []
                    for checkbox in checkboxes:
                        label = checkbox.get_attribute("aria-label") or ""
                        label_map.append((label.strip().lower(), checkbox))

                    # Rebuild clean choices list directly from checkbox labels
                    choices_text = [label for label, _ in label_map]

                    # Get GPT response
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=True)
                    print(f"[GPT Choice Answer Raw] {ai_answer}")

                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=True)
                    if selected_indices:
                        for idx in selected_indices:
                            if 0 <= idx < len(label_map):
                                label_text, checkbox_element = label_map[idx]
                                driver.execute_script("arguments[0].scrollIntoView(true);", checkbox_element)
                                driver.execute_script("arguments[0].click();", checkbox_element)
                                print(f"✓ Checked: {label_text}")
                            else:
                                print(f"⚠️ GPT selected index {idx} out of bounds.")
                    else:
                        print("⚠️ GPT was unsure — checkboxes skipped.")
                    continue

                # === DROPDOWNS ===
                dropdowns = question.find_elements(By.CSS_SELECTOR, 'div[role="listbox"]')
                if dropdowns:
                    dropdown_btn = dropdowns[0].find_element(By.CSS_SELECTOR, 'div[role="button"]')
                    dropdown_btn.click()
                    time.sleep(1)
                    options = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
                    choices_text = extract_choices(options)
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=False)
                    print(f"[GPT Raw Answer] {ai_answer}")
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text))
                    if selected_indices:
                        expected_text = choices_text[selected_indices[0]].lower().strip()
                        for option in options:
                            if expected_text in option.text.lower():
                                driver.execute_script("arguments[0].scrollIntoView(true);", option)
                                driver.execute_script("arguments[0].click();", option)
                                print(f"✓ Dropdown: {expected_text}")
                                break
                    else:
                        print("⚠️ GPT was unsure — dropdown skipped.")
                    continue

                print("⚠️ Unknown input type.")
            except Exception as e:
                print(f"[ERROR] Question {q_index}: {e}")

        print("\n✅ All questions filled (form not submitted). Review in browser.")
        input("🔍 Press Enter to exit...")

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
