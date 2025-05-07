# 🔍 AI-Powered Web Form and Questionnaire Auto-Filler

This project automates the extraction, answering, and autofill of web-based questionnaires (e.g., Google Forms, JotForm, CENTRL) using **Playwright, Selenium, and OpenAI GPT-4**. It supports structured and unstructured form types, dynamically rendered UIs, and uses LLMs to reason over HTML content for realistic, context-aware answers.

---

## ✨ Features

- **💡 GPT-Driven Question Understanding:**
  - Uses GPT-4 or GPT-4 Turbo to parse HTML or structured fields.
  - Identifies question types (text, radio, checkbox, select) and generates relevant answers.

- **📄 Multi-Platform Support:**
  - Works with Google Forms, JotForm, CENTRL, and other HTML-based questionnaires.

- **🧠 Human-Like Scrolling & Section Handling:**
  - Mimics realistic user scrolling with Playwright.
  - Supports multi-section navigation with Next Section detection.

- **✅ Multi-Model Answer Generation:**
  - GPT-4 handles both question extraction and auto-answering.
  - Uses prompt-engineering with deterministic output for radio/checkbox formats.

- **📦 Form Auto-Fill Capabilities:**
  - Fills text fields, selects dropdowns, clicks checkboxes and radio buttons.
  - Includes fallback logic for ambiguous inputs.

- **🧪 Debug & Review:**
  - Form is filled but **not submitted**.
  - Logs all generated answers.

---
## 🛠️ Tech Stack

- **Python 3.8+**
- **Playwright** for dynamic browser automation (CENTRL, JotForm)
- **Selenium** for Google Forms
- **OpenAI GPT-4/GPT-4 Turbo** for answering questions
- **BeautifulSoup** for HTML parsing

---

## 💻 Use Cases

- CENTRL compliance questionnaires
- Google Form assessments
- Internal due diligence portals
- Auto-filling vendor onboarding forms

---

## 📂 Example Outputs

- `centrl_questions_gpt.json`: Questions extracted from CENTRL platform
- `extracted_answers_from_html.json`: AI-filled answers for generic HTML form
- `debug_all_sections.html`: Snapshot of all questionnaire sections from CENTRL

---

## ⚙️ Configuration

Edit the following variables depending on the use case:

```python
LOGIN_EMAIL = "bshetty@oncentrl.com"
LOGIN_PASSWORD = "your-password"
OPENAI_API_KEY = "sk-xxxx"
QUESTIONNAIRE_URL = "https://web.oncentrl.com/..."
TARGET_URL = "https://formprovider.com/..."
```

---

## 🚀 Running the Projects

### 1. CENTRL Questionnaire Extractor
```bash
python centrl_extractor.py
```

### 2. JotForm/Generic HTML Form Autofill
```bash
python html_autofill_gpt.py
```

### 3. Google Form Auto-Fill via Selenium
```bash
python google_form_autofill.py
```

---

## 📈 Future Enhancements

- [ ] Capture and preserve form subsection names
- [ ] Add visual debugger for mismatched answers
- [ ] Plug-in document-based RAG for better grounding


## 🤖 Built With
- OpenAI GPT-4 Turbo
- Microsoft Playwright
- Selenium
- LangGraph (experimental)
- BeautifulSoup
- JSON

