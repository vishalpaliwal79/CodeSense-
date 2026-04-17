from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    driver = webdriver.Chrome(options=options)
    driver.get("http://127.0.0.1:5000")
    for entry in driver.get_log('browser'):
        print(entry)
    driver.quit()
except Exception as e:
    print("Error:", e)
