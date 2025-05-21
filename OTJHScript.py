import os
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv

# === LOAD .env VARIABLES ===
load_dotenv()
USERNAME = os.getenv("BUD_USERNAME")
PASSWORD = os.getenv("BUD_PASSWORD")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

LOGIN_URL = "https://web.bud.co.uk/learningportal/learner/login"
LEARNER_URL = "https://web.bud.co.uk/learningportal/learner"

# === BROWSER SETUP ===
def start_browser():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(options=options)

# === LOGIN ===
def login(driver):
    driver.get(LOGIN_URL)
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "password").send_keys(Keys.RETURN)
    time.sleep(5)

# === GET MODULES ===
def get_modules(driver):
    driver.get(LEARNER_URL)
    time.sleep(3)
    driver.find_element(By.CSS_SELECTOR, "button.continue-learning").click()
    time.sleep(3)

    modules = driver.find_elements(By.CSS_SELECTOR, "a.card-link")
    non_numbered = [m for m in modules if not re.search(r'\bPC\d+\b', m.text)]
    module_titles = [m.text.strip() for m in non_numbered]

    print("\nAvailable Modules:")
    for idx, title in enumerate(module_titles):
        print(f"{idx+1}. {title}")

    choice = int(input("\nEnter the number of the module you want to log hours for: ")) - 1
    return non_numbered[choice], module_titles[choice]

# === GET DETAILS ===
def get_log_details():
    total_hours = int(input("Enter number of hours to log (max 8): "))
    repeat = input("Do you want to log this weekly? (y/n): ").strip().lower()

    weeks = 1
    if repeat == 'y':
        weeks = int(input("How many weeks?: "))

    start_date_str = input("Enter the start date (YYYY-MM-DD): ")
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

    context_prompt = input("Optionally, enter a short summary of what was done in the module (or press Enter and the AI will do it for you): ").strip()

    return total_hours, start_date, weeks, context_prompt

# === AI COMMENT GENERATION ===
def generate_comment(module_title, log_date, context_prompt):
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    user_prompt = f"Write a short, professional summary for a training log entry for the module '{module_title}' on {log_date.strftime('%d %B %Y')}."
    if context_prompt:
        user_prompt += f" Focus on: {context_prompt}"

    messages = [
        {"role": "system", "content": "You are an assistant helping an apprentice summarize off-the-job learning logs in 1–2 sentences professionally."},
        {"role": "user", "content": user_prompt}
    ]

    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.5
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠️ AI failed, using fallback. Error: {e}")
        return f"Worked on {module_title} on {log_date.strftime('%d %B %Y')}."

# === LOG THE HOURS ===
def log_hours(driver, module_link, module_title, total_hours, start_date, weeks, context_prompt):
    module_link.click()
    time.sleep(3)

    driver.find_element(By.LINK_TEXT, "Off the Job Hours").click()
    time.sleep(2)

    for i in range(weeks):
        log_date = start_date + timedelta(days=i*7)
        driver.find_element(By.XPATH, "//span[contains(text(),'Add OTJ Hours')]").click()
        time.sleep(1)

        driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='date']").clear()
        driver.find_element(By.CSS_SELECTOR, "input[formcontrolname='date']").send_keys(log_date.strftime("%d/%m/%Y"))
        driver.find_element(By.CSS_SELECTOR, "select[formcontrolname='startTimeHours']").send_keys("09")
        driver.find_element(By.CSS_SELECTOR, "select[formcontrolname='startTimeMinutes']").send_keys("00")
        driver.find_element(By.CSS_SELECTOR, "select[formcontrolname='endTimeHours']").send_keys("17")
        driver.find_element(By.CSS_SELECTOR, "select[formcontrolname='endTimeMinutes']").send_keys("00")

        comment = generate_comment(module_title, log_date, context_prompt)
        driver.find_element(By.CSS_SELECTOR, "textarea[formcontrolname='comments']").send_keys(comment)
        driver.find_element(By.XPATH, "//button[contains(text(),'Add')]").click()
        time.sleep(2)

        print(f"✔️ Logged OTJ for {log_date.strftime('%d %b %Y')}")

# === MAIN ===
if __name__ == "__main__":
    print("🔐 Starting automation...")
    driver = start_browser()
    login(driver)
    module_element, module_title = get_modules(driver)
    total_hours, start_date, weeks, context_prompt = get_log_details()
    log_hours(driver, module_element, module_title, total_hours, start_date, weeks, context_prompt)
    print("\n✅ All logs submitted. Check: ", driver.current_url)
    driver.quit()