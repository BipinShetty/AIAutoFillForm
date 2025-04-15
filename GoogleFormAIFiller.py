import time
import openai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROMEDRIVER_PATH = "/your/path/to/chromedriver"  # update this
openai.api_key = "your_openai_api_key"  # update this

def generate_ai_answer_for_text(question_text):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that answers questions concisely."},
        {"role": "user", "content": question_text}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=100
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[ERROR] OpenAI API error (text answer): {e}")
        return "N/A"

def generate_ai_answer_for_choices(question_text, choices, multi_select=False):
    if not any(choices):
        return ""
    choices_prompt = "\n".join([f"{i+1}. {c}" for i, c in enumerate(choices)])
    instruction = "Select the best choices (comma-separated numbers)." if multi_select else "Select the best choice (number)."
    prompt = f"Question: {question_text}\nChoices:\n{choices_prompt}\n{instruction}\nAnswer:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=20
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[ERROR] OpenAI API error (choice answer): {e}")
        return ""

def parse_choices_indices(answer_text, max_index, multi_select=False):
    try:
        parts = answer_text.replace('.', '').replace('and', ',').replace(';', ',').split(',')
        indices = [int(p.strip()) - 1 for p in parts if p.strip().isdigit()]
        indices = [i for i in indices if 0 <= i < max_index]
        return list(set(indices)) if multi_select else [indices[0]] if indices else []
    except Exception as e:
        print(f"[ERROR] Parsing AI answer indices: {e}")
        return []

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

def main():
    service = Service(executable_path=CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=options)
    actions = ActionChains(driver)

    try:
        form_url = 'https://docs.google.com/forms/d/1uMkzOGtiVN_VqtPPjTInpd1nP64Ii_3vdMaNlwU6Z8Y/viewform'
        driver.get(form_url)
        time.sleep(4)

        question_containers = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        print(f"Found {len(question_containers)} questions.")

        for q_index, question in enumerate(question_containers, start=1):
            try:
                q_text_els = question.find_elements(By.CSS_SELECTOR, 'div.freebirdFormviewerComponentsQuestionBaseTitle')
                question_text = q_text_els[0].text.strip() if q_text_els else ""
                print(f"\nQuestion {q_index}: {question_text}")

                if "email" in question_text.lower():
                    print("Detected email question — skipping actual fill.")
                    continue

                text_inputs = question.find_elements(By.CSS_SELECTOR, 'input[type="text"], textarea')
                if text_inputs:
                    answer = generate_ai_answer_for_text(question_text)
                    print(f"[AI Text Answer] → {answer}")
                    continue

                radios = question.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                if radios:
                    choices_text = extract_choices(radios)
                    print(f"[Multiple Choice Options] {choices_text}")
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=False)
                    print(f"[AI Selected] {ai_answer}")
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=False)
                    if selected_indices:
                        print(f"[AI Selected Index] {selected_indices[0]} → {choices_text[selected_indices[0]]}")
                    continue

                checkboxes = question.find_elements(By.CSS_SELECTOR, 'div[role="checkbox"]')
                if checkboxes:
                    choices_text = extract_choices(checkboxes)
                    print(f"[Checkbox Options] {choices_text}")
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=True)
                    print(f"[AI Selected] {ai_answer}")
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=True)
                    for idx in selected_indices:
                        print(f"[AI Selected Index] {idx} → {choices_text[idx]}")
                    continue

                dropdowns = question.find_elements(By.CSS_SELECTOR, 'div[role="listbox"]')
                if dropdowns:
                    dropdown_btn = dropdowns[0].find_element(By.CSS_SELECTOR, 'div[role="button"]')
                    dropdown_btn.click()
                    time.sleep(1)
                    options = driver.find_elements(By.CSS_SELECTOR, 'div[role="option"]')
                    choices_text = extract_choices(options)
                    print(f"[Dropdown Options] {choices_text}")
                    ai_answer = generate_ai_answer_for_choices(question_text, choices_text, multi_select=False)
                    print(f"[AI Dropdown Selection] {ai_answer}")
                    selected_indices = parse_choices_indices(ai_answer, len(choices_text), multi_select=False)
                    if selected_indices:
                        print(f"[AI Selected Index] {selected_indices[0]} → {choices_text[selected_indices[0]]}")
                    continue

                print("Question type not recognized or no input found.")
            except Exception as e:
                print(f"[ERROR] Processing question {q_index}: {e}")

        print("\n⏭️ Skipped form submission. AI-selected answers have been printed above.")

    finally:
        driver.quit()

if __name__ == '__main__':
    main()
