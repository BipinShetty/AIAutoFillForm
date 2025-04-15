import time
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains

# === CONFIG ===
CHROMEDRIVER_PATH = "chromedriver-mac-x64/chromedriver"  # 🔁 UPDATE THIS
openai.api_key = ""       # 🔁 UPDATE THIS

# === GPT TEXT INPUT HANDLER ===
def generate_ai_answer_for_text(question_text):
    prompt = f"Answer the following question clearly and accurately.\n\nQuestion: {question_text}\nAnswer:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=100
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Text answer: {e}")
        return "N/A"

# === GPT CHOICE HANDLER WITH ANTI-HALLUCINATION LOGIC ===
def generate_ai_answer_for_choices(question_text, choices, multi_select=False, retries=1):
    if not any(choices):
        return ""

    instruction = (
        "You are answering a form. Choose only from the listed choices.\n"
        "Return only the option number(s). If none match, return '0'. Do NOT explain."
    )

    choices_prompt = "\n".join([f"{i+1}. {c}" for i, c in enumerate(choices)])
    selection_note = (
        "You may select more than one. Use comma-separated numbers like '2,3'." if multi_select
        else "Select only one. Use a single number like '2'."
    )

    full_prompt = f"{instruction}\n\nQuestion: {question_text}\nChoices:\n{choices_prompt}\n{selection_note}\nAnswer:"

    for attempt in range(retries + 1):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0,
                max_tokens=10
            )
            answer = response.choices[0].message.content.strip()
            if answer and any(char.isdigit() for char in answer):
                return answer
        except Exception as e:
            print(f"[ERROR] GPT (retry {attempt}) failed: {e}")
    return "0"

# === CHOICE PARSER ===
def parse_choices_indices(answer_text, max_index, multi_select=False):
    try:
        parts = answer_text.replace('.', '').replace('and', ',').replace(';', ',').split(',')
        indices = [int(p.strip()) - 1 for p in parts if p.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < max_index]
        return list(set(indices)) if multi_select else [indices[0]] if indices else []
    except Exception as e:
        print(f"[ERROR] Parsing indices: {e}")
        return []

# === EXTRACT CHOICE LABELS ===
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

# === MAIN WORKFLOW ===
def main():
    service = Service(executable_path=CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    actions = ActionChains(driver)

    try:
        driver.get("https://docs.google.com/forms/d/1uMkzOGtiVN_VqtPPjTInpd1nP64Ii_3vdMaNlwU6Z8Y/viewform")
        time.sleep(4)

        question_containers = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        print(f"Found {len(question_containers)} questions.")

        for q_index, question in enumerate(question_containers, start=1):
            try:
                q_text_el = question.find_elements(By.CSS_SELECTOR, 'div.freebirdFormviewerComponentsQuestionBaseTitle')
                question_text = q_text_el[0].text.strip() if q_text_el else ""
                print(f"\nQ{q_index}: {question_text}")

                # === EMAIL HANDLER ===
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

                # === RADIO BUTTONS ===
                radios = question.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                if radios:
                    choices_text = extract_choices(radios)
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=False)
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=False)
                    if selected_indices and selected_indices[0] >= 0:
                        el = radios[selected_indices[0]]
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                        driver.execute_script("arguments[0].click();", el)
                        print(f"✓ Selected: {choices_text[selected_indices[0]]}")
                    else:
                        print("⚠️ GPT was unsure — radio skipped.")
                    continue

                # === CHECKBOXES ===
                checkboxes = question.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                if checkboxes:
                    choices_text = extract_choices(checkboxes)
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=True)
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=True)
                    if selected_indices:
                        for idx in selected_indices:
                            el = checkboxes[idx]
                            driver.execute_script("arguments[0].scrollIntoView(true);", el)
                            driver.execute_script("arguments[0].click();", el)
                        print(f"✓ Checked: {[choices_text[i] for i in selected_indices]}")
                    else:
                        print("⚠️ GPT was unsure — checkboxes skipped.")
                    continue

                # === DROPDOWN ===
                dropdowns = question.find_elements(By.CSS_SELECTOR, 'div[role="listbox"]')
                if dropdowns:
                    dropdown_btn = dropdowns[0].find_element(By.CSS_SELECTOR, 'div[role="button"]')
                    dropdown_btn.click()
                    time.sleep(1)
                    options = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
                    choices_text = extract_choices(options)
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=False)
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=False)
                    if selected_indices:
                        options[selected_indices[0]].click()
                        print(f"✓ Dropdown: {choices_text[selected_indices[0]]}")
                    else:
                        print("⚠️ GPT was unsure — dropdown skipped.")
                    continue

                print("⚠️ Unknown input type.")
            except Exception as e:
                print(f"[ERROR] Question {q_index}: {e}")

        print("\n✅ All questions filled (form not submitted). Review in browser.")
        input("🔍 Press Enter to close...")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
