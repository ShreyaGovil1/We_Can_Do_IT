import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import os
from io import StringIO
import pandas as pd
from dotenv import load_dotenv
load_dotenv()


st.set_page_config(page_title="LinkedIn Easy Apply Bot", layout="centered")

st.title("🤖 LinkedIn Easy Apply Automation")

email = os.getenv("LINKEDIN_EMAIL")
password = os.getenv("LINKEDIN_PASSWORD")
keywords = st.text_input("Job Keywords", value="python developer")
location = st.text_input("Location", value="Worldwide")
phone_number = st.text_input("Phone Number", max_chars=15)

experience_levels = {
    "Internship": "1",
    "Entry level": "2",
    "Associate": "3",
    "Mid-Senior level": "4",
    "Director": "5",
    "Executive": "6",
    "All Levels": ""
}
job_types = {
    "All": "",
    "Remote": "2",
    "Hybrid": "3",
    "On-site": "1",
}
selected_job_type = st.selectbox("Workplace Type", list(job_types.keys()))
selected_level = st.selectbox("Experience Level", list(experience_levels.keys()))
company_name = st.text_input("Filter by Company (Optional)")
resume_file = st.file_uploader("Upload Your Resume (PDF)", type=["pdf"])

submit = st.button("Start Auto Apply")
applied_log = []

def human_sleep(min_sec=2, max_sec=5):
    time.sleep(random.uniform(min_sec, max_sec))

def login_to_linkedin(driver, email, password):
    driver.get("https://www.linkedin.com/login")
    human_sleep()
    driver.find_element(By.ID, "username").send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    human_sleep(3, 6)

def handle_easy_apply(driver, resume_path, phone_number):
    while True:
        human_sleep(2, 4)
        try:
            # Upload resume if required
            try:
                upload = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                upload.send_keys(resume_path)
                st.write("📄 Resume uploaded.")
            except:
                pass

            # Fill phone number if available
            try:
                phone_field = driver.find_element(By.XPATH,"//label[normalize-space(text())='Phone' or normalize-space(text())='Mobile phone number']/following-sibling::input")
                phone_field.clear()
                phone_field.send_keys(phone_number)
                st.write("📱 Phone number filled.")
            except Exception as e:
                st.warning(f"⚠️ Phone input not found: {e}")


            # Click next or submit
            try:
                next_btn = driver.find_element(By.XPATH, "//button/span[text()='Next']/..")
                next_btn.click()
                st.write("➡️ Clicked Next.")
            except:
                try:
                    submit_btn = driver.find_element(By.XPATH, "//button/span[text()='Submit']/..")
                    submit_btn.click()
                    st.success("✅ Applied successfully.")
                    return True
                except:
                    st.warning("⚠️ No Next/Submit found. Possibly complex form.")
                    return False
        except Exception as e:
            st.error(f"❌ Multi-step error: {str(e)}")
            return False

def apply_to_jobs(driver, resume_path, keywords, location, exp_code, company_name, job_type_code, phone_number, applied_log):
    exp_code = experience_levels[selected_level]
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_AL=true&f_WT=2"
    if exp_code:
        search_url += f"&f_E={exp_code}"
    if company_name:
        search_url += f"&f_C={company_name.replace(' ', '%20')}"
    if job_type_code:
        search_url += f"&f_WT={job_type_code}"  # Workplace Type
    driver.get(search_url)
    human_sleep(4, 6)

    job_cards = driver.find_elements(By.CLASS_NAME, 'job-card-container--clickable')
    st.write(f"🔍 Found {len(job_cards)} jobs.")

    for job in job_cards[:5]:
        try:
            job.click()
            human_sleep()

            easy_apply = driver.find_element(By.CLASS_NAME, "jobs-apply-button")
            easy_apply.click()
            human_sleep()

            success = handle_easy_apply(driver, resume_path, phone_number)
            if success:
                title = driver.find_element(By.CLASS_NAME, 'jobs-unified-top-card__job-title').text
                job_link = driver.current_url
                applied_log.append({"Job Title": title, "Link": job_link})
            else:
                driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']").click()
                human_sleep()
        except:
            st.info("⏩ Skipping: Not Easy Apply or application failed.")
        human_sleep(3, 6)

if submit and email and password and phone_number and keywords and location and resume_file:
    with st.spinner("Setting up browser and logging in..."):
        resume_path = os.path.abspath(resume_file.name)
        with open(resume_path, "wb") as f:
            f.write(resume_file.getbuffer())

        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            login_to_linkedin(driver, email, password)
            apply_to_jobs(
                driver, resume_path, keywords, location,
                experience_levels[selected_level], company_name,
                job_types[selected_job_type], phone_number, applied_log
            )
        finally:
            driver.quit()

    if applied_log:
        df = pd.DataFrame(applied_log)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Application Log", csv, "applied_jobs.csv", "text/csv")
else:
    st.info("Please fill in all fields and upload your resume to begin.")