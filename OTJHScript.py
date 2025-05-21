import os
import openai
import time
import re
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import chromedriver_autoinstaller
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === LOAD .env VARIABLES ===
load_dotenv()
USERNAME = os.getenv("BUD_USERNAME")
PASSWORD = os.getenv("BUD_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LOGIN_URL = "https://web.bud.co.uk/learningportal/learner/login"
LEARNER_URL = "https://web.bud.co.uk/learningportal/learner"

# === BROWSER SETUP ===
def start_browser():
    # Automatically install and use matching chromedriver version
    chromedriver_autoinstaller.install()

    options = Options()
    options.add_argument("--headless")
    #options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    return webdriver.Chrome(options=options)

# === LOGIN ===
def login(driver):
    driver.get("https://web.bud.co.uk/learningportal/learner/login")

    # Wait for and accept the cookie banner if present
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        ).click()
        time.sleep(1)
        driver.refresh()
    except:
        pass

    # Wait for the login form to appear
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "Username"))
    )

    driver.find_element(By.ID, "Username").send_keys(USERNAME)
    driver.find_element(By.ID, "Password").send_keys(PASSWORD)
    driver.find_element(By.ID, "Password").send_keys(Keys.RETURN)

    # Wait for dashboard to load
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "lp-card"))
    )

# === GET MODULES ===
def get_modules(driver):
    driver.get(LEARNER_URL)
    time.sleep(3)
    driver.find_element(By.CSS_SELECTOR, "button.continue-learning").click()
    time.sleep(3)

    timeout = time.time() + 15
    modules = []

    while time.time() < timeout:
        modules = driver.find_elements(By.CSS_SELECTOR, "div[data-cy='TableElement_ActivityName'] a")
        if any(m.text.strip() for m in modules):
            break
        time.sleep(0.5)

    print("\n📚 Available Modules:")
    for idx, m in enumerate(modules):
        title = m.text.strip()
        if title:
            print(f"{idx + 1}. {title}")

    choice = int(input("\nEnter the number for the module: ")) - 1
    return modules[choice], modules[choice].text.strip()

# === GET DETAILS ===
def get_log_details():
    total_hours = int(input("Enter how many hours to log for one day (max 8): "))
    repeat = input("Do you want this to log multiple? (y/n): ").strip().lower()

    weeks = 1
    if repeat == 'y':
        weeks = int(input("How many weeks to log (4 is 1 entry every week for 4 weeks): "))

    start_date_str = input("Enter the start date (DD/MM/YYYY): ")
    start_date = datetime.strptime(start_date_str, "%d/%m/%Y")

    context_prompt = input("Press Enter so AI can write something about module (or write a comment which the AI will buff up): ").strip()

    return total_hours, start_date, weeks, context_prompt

# === AI COMMENT GENERATION ===
def generate_comment(module_title, log_date, context_prompt):
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    user_prompt = f"Write a short, professional summary about what you did (max 255 characters) for the module '{module_title}' on {log_date.strftime('%d %B %Y')} as you are an apprentice."
    if context_prompt:
        user_prompt += f" Focus on: {context_prompt}"

    messages = [
        {"role": "system", "content": "You are the apprentice summarising their off-the-job learning logs in max 255 characters professionally."},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=messages,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
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

        time.sleep(5)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label='date input']"))
        )
        date_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label='date input']")
        date_input.click()
        date_input.send_keys(Keys.END)
        for _ in range(10):
            date_input.send_keys(Keys.BACKSPACE)
        date_input.send_keys(log_date.strftime("%d/%m/%Y"))
        time.sleep(5)
        time_inputs = driver.find_elements(By.CSS_SELECTOR, "timepicker-input select.time-split")
        if len(time_inputs) >= 4:
            time_inputs[0].send_keys("09")  # Start hours
            time_inputs[1].send_keys("00")  # Start minutes
            time_inputs[2].send_keys("17")  # End hours
            time_inputs[3].send_keys("00")  # End minutes
        comment = generate_comment(module_title, log_date, context_prompt)
        comment_box = driver.find_element(By.CSS_SELECTOR, "textarea[data-cy='comments-input']")
        comment_box.clear()
        comment_box.send_keys(comment)
        print("⏳ Please wait, OTJH are being added now...")

        # Wait for the Add button to be clickable using the updated selector
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-cy='edit-otjh-modal-submit-button'] button"))
        ).click()
        time.sleep(2)
    print("✅ All Off-the-Job Hours have been successfully logged!")

    # Generate link to the module's OTJH page
    current_url = driver.current_url
    if "/activity/" in current_url:
        otjh_url = current_url.rstrip("/") + "/otjhs"
        print(f"🔗 You can review your OTJH log here: {otjh_url}")

# === MAIN ===
if __name__ == "__main__":
    driver = start_browser()
    login(driver)
    module_element, module_title = get_modules(driver)
    total_hours, start_date, weeks, context_prompt = get_log_details()
    log_hours(driver, module_element, module_title, total_hours, start_date, weeks, context_prompt)
    driver.quit()