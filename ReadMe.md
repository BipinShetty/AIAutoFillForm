# Google Form Auto Filler Using Selenium & OpenAI GPT

This project automatically analyzes and answers Google Form questions using OpenAI's GPT-3.5 Turbo and simulates how a human would interpret and respond to them. It supports text fields, multiple choice, checkboxes, and dropdown menus — without submitting the form, allowing for review of AI-selected answers.

---

## ✨ Features

- ✅ Extracts and interprets form questions using Selenium
- 🤖 Uses OpenAI's GPT-3.5 Turbo to generate contextually relevant answers
- 📋 Supports:
  - Short and long text answers
  - Multiple choice (radio buttons)
  - Checkboxes (multi-select)
  - Dropdowns
- 🔍 Logs selected AI answers for each question
- ❌ Skips actual submission to allow answer verification

---

## 📦 Requirements

- Python 3.8+
- Google Chrome installed
- Compatible ChromeDriver matching your Chrome version
- OpenAI API key

---

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/google-form-autofill-ai.git
cd google-form-autofill-ai
