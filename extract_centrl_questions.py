import asyncio
import json
import re
from bs4 import BeautifulSoup
from openai import OpenAI
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# ====== CONFIG ======
LOGIN_EMAIL = "bshetty@oncentrl.com"
LOGIN_PASSWORD = "oprahWIN1233"
LOGIN_URL = "https://web.oncentrl.com/#/login"
QUESTIONNAIRE_URL = "https://web.oncentrl.com/#/cc/questionnaire/details/answering/ondemand/147212?searchText="
OUTPUT_FILE = "centrl_questions_gpt.json"
OPENAI_API_KEY = "sk-xxxx"  # 🔑 Replace with your OpenAI API key

# GPT Client setup
client = OpenAI(api_key=OPENAI_API_KEY)

async def navigate_and_capture_all_sections(page, max_sections=50):
    section_counter = 0
    html_chunks = []

    try:
        while section_counter < max_sections:
            # Scroll and capture the current section
            await human_like_scroll(page, container_selector="#pqv-body-right", step=250, pause=400)

            current_html = await page.evaluate("() => document.querySelector('body').innerHTML")
            html_chunks.append(f"<!-- Section {section_counter + 1} -->\n{current_html}")

            # Locate the Next Section button
            next_btn = await page.query_selector('div.submit-btn.primary:has-text("Next Section")')
            if not next_btn:
                print("🛑 No more 'Next Section' button found.")
                break

            next_btn_class = await next_btn.get_attribute("class") or ""
            if "disabled" in next_btn_class:
                print("🛑 'Next Section' button is present but disabled.")
                break

            # Track current question count for smarter wait
            prev_count = await page.evaluate(
                "() => document.querySelectorAll('span.question-txt, div.question-title').length"
            )

            await next_btn.scroll_into_view_if_needed()
            await next_btn.click()
            section_counter += 1
            print(f"🔄 Clicked 'Next Section' button #{section_counter}")

            try:
                await page.wait_for_function(
                    f"document.querySelectorAll('span.question-txt, div.question-title').length > {prev_count}",
                    timeout=8000
                )
            except Exception:
                print(f"⚠️ Timeout waiting for new questions after section {section_counter}")

            await page.wait_for_timeout(1500)

        # Final scroll & capture in case final section didn’t have a button
        await human_like_scroll(page, container_selector="#pqv-body-right", step=250, pause=400)
        final_html = await page.evaluate("() => document.querySelector('body').innerHTML")
        html_chunks.append(f"<!-- Final Section -->\n{final_html}")

    except Exception as e:
        if "closed" in str(e).lower():
            print("❌ Browser or page was unexpectedly closed. Exiting gracefully.")
        else:
            print(f"⚠️ Unexpected error during section navigation: {e}")

    # Final scroll to bottom
    try:
        await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"⚠️ Could not scroll page: {e}")

    # Save all HTML chunks
    try:
        combined_html = "\n<!-- ==== End of Section ==== -->\n".join(html_chunks)
        with open("debug_all_sections.html", "w", encoding="utf-8") as f:
            f.write(combined_html)
        print(f"✅ Fetched and saved {section_counter + 1} sections to 'debug_all_sections.html'.")
    except Exception as e:
        print(f"❌ Failed to save HTML: {e}")

    try:
        await page.context.browser.close()
    except Exception:
        print("⚠️ Could not close browser cleanly.")

    return combined_html


async def human_like_scroll(page, container_selector="#pqv-body-right", step=400, pause=500, max_attempts=100):
    """
    Scrolls a container until it reaches the bottom, mimicking human behavior.

    :param page: Playwright Page
    :param container_selector: CSS selector for scrollable container
    :param step: Pixels to scroll each time
    :param pause: Delay between scrolls (ms)
    :param max_attempts: Safety limit to prevent infinite loops
    """
    attempt = 0

    while attempt < max_attempts:
        scrolled = await page.evaluate(
            f'''() => {{
                const el = document.querySelector("{container_selector}");
                if (!el) return false;

                const prevScrollTop = el.scrollTop;
                el.scrollTop += {step};

                // If we're already at the bottom
                return el.scrollTop > prevScrollTop;
            }}'''
        )

        if not scrolled:
            print("✅ Reached bottom of scrollable container.")
            break

        await page.wait_for_timeout(pause)
        attempt += 1

    if attempt >= max_attempts:
        print("⚠️ Reached max scroll attempts. There might be more content.")


# ========== Step 1: Login and get full questionnaire HTML ==========
async def  fetch_questionnaire_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        print("🌐 Navigating to login page...")
        await page.goto(LOGIN_URL)
        await page.wait_for_timeout(2000)

        # Email step (robust)
        try:
            await page.goto(LOGIN_URL, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            email_input_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="Email"]',
                'input'
            ]

            email_found = False
            for selector in email_input_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.fill(selector, LOGIN_EMAIL)
                    print(f"✅ Email filled using selector: {selector}")
                    email_found = True
                    break
                except:
                    continue

            if not email_found:
                raise Exception("❌ Email field not found.")

            await page.click('button:has-text("Continue")')
            await page.wait_for_timeout(2000)

            await page.wait_for_selector('input[type="password"]', timeout=10000)
            await page.fill('input[type="password"]', LOGIN_PASSWORD)
            await page.click('button:has-text("Login")')

            await page.wait_for_timeout(5000)

        except Exception as e:
            print(f"❌ Login failed: {e}")
            await page.screenshot(path="login-failure.png")
            await browser.close()
            return


        # Go to questionnaire
        print("🧾 Navigating to questionnaire...")
        await page.goto(QUESTIONNAIRE_URL)
        await page.wait_for_timeout(6000)

        # Try to click 'Start Answering' if present
        try:
            start_btn = await page.query_selector('div.submit-btn.primary:has-text("Start Answering")')
            if start_btn:
                await start_btn.scroll_into_view_if_needed()
                await start_btn.click()
                print("✅ Clicked 'Start Answering' button.")
                await page.wait_for_timeout(3000)
            else:
                print("ℹ️ 'Start Answering' button not found — continuing without clicking it.")
        except Exception as e:
            print(f"⚠️ Error while handling 'Start Answering' button: {e}")

        html = await navigate_and_capture_all_sections(page)


        # ... you can now extract questions from `html` or pass it downstream
        print("✅ Done capturing questionnaire.")

        return html



# ========== Step 2: Use GPT-4 to extract questions ==========
# ========== Step 2: Preprocess HTML ==========


def extract_question_blocks(raw_html):

    soup = BeautifulSoup(raw_html, "html.parser")

    # Look for common tags used for question text
    question_tags = soup.select("span.question-txt, div.question-title")
    print(f"🔍 Found {len(question_tags)} question tags in HTML.")

    questions = []
    for i, tag in enumerate(question_tags, start=1):
        text = tag.get_text(strip=True)
        if text:
            questions.append({
                "question_id": f"q_{i}",
                "section": None,
                "question": text,
                "type": "unknown",
                "options": []
            })

    return questions



# ========== Step 3: Chunk HTML and call GPT ==========
def call_gpt_on_chunks(chunks):
    extracted_questions = []

    for i, chunk in enumerate(chunks):
        print(f"🤖 Calling GPT-4 for chunk {i+1}...")
        prompt = f"""
You are an expert in parsing questionnaires.

Extract all questions from the following plain text and return as a JSON list of objects with keys:
- section (always null)
- question_id (use provided ID or generate like q_1, q_2...)
- question (clean readable text)
- type (always "unknown")
- options (always empty list)

Only respond with a JSON array like:
[
  {{
    "section": null,
    "question_id": "q_1",
    "question": "Does the firm have a BCP plan?",
    "type": "unknown",
    "options": []
  }},
  ...
]

Input:
{chunk}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You extract structured questionnaire questions from plain text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )
            data = response.choices[0].message.content

            try:
                parsed = json.loads(data)
                extracted_questions.extend(parsed)
            except json.JSONDecodeError:
                print(f"⚠️ GPT returned invalid JSON for chunk {i+1}, skipping.")
                print(f"🔎 Raw output:\n{data[:300]}...\n")
        except Exception as e:
            print(f"⚠️ GPT failed for chunk {i+1}: {e}")

    return extracted_questions


# ========== Step 4: Save ==========
def save_questions(questions):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(questions, f, indent=2)
    print(f"📦 Saved {len(questions)} questions to {OUTPUT_FILE}")


# ========== Main ==========
async def main():
    html = await fetch_questionnaire_html()
    blocks = extract_question_blocks(html)
    chunks = ["\n".join([json.dumps(b) for b in blocks[i:i + 20]]) for i in range(0, len(blocks), 20)]
    questions = call_gpt_on_chunks(chunks)
    save_questions(questions)

if __name__ == "__main__":
    asyncio.run(main())