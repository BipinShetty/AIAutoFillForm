# Google Form Auto Filler Using Selenium & OpenAI GPT

This project automatically analyzes and answers Google Form questions using OpenAI's GPT-3.5 Turbo. It simulates how a human would interpret and respond to form questions across various input types (text, multiple choice, checkboxes, and dropdown menus) and fills in the form accordingly—without submitting it, so you can review the AI-selected responses before final submission.
![Screen Shot 2025-04-15 at 1 11 11 PM](https://github.com/user-attachments/assets/a30aa0ee-7335-487f-9821-5286607216e7)

---

## ✨ Features

- **Automated Question Extraction:** Uses Selenium to locate and extract questions and options from Google Forms.
- **GPT-Powered Answers:** Leverages OpenAI's GPT-3.5 Turbo to generate concise, context-aware responses.
- **Multi-Input Support:**  
  - **Text Fields:** Fills short and long text responses.  
  - **Multiple Choice (Radio Buttons):** Uses robust prompts and JavaScript click execution for reliable option selection.  
  - **Checkboxes (Multi-Select):** Supports accurate multi-selection.  
  - **Dropdowns:** Selects dropdown options correctly.
- **Enhanced Accuracy:** Incorporates few-shot examples and strict, deterministic prompting to minimize hallucinations and ensure answers are drawn solely from the provided choices.
- **Review Mode:** The form is auto-filled but not submitted, allowing manual verification and adjustment.
- **Logging:** Displays the AI’s selected answers for each question in the console.

---

## 📦 Requirements

- **Python 3.8+**
- **Google Chrome** (latest version recommended)
- A compatible **ChromeDriver** (download from [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads))
- **OpenAI API key**

---

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/google-form-autofill-ai.git
   cd google-form-autofill-ai
