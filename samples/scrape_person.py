import os
import json
import urllib.parse
import logging
from pathlib import Path
from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

log_file = open("z:\\scrape.log", encoding="utf-8", mode="a")
logging.basicConfig(level=logging.INFO,
                    stream=log_file,
                    format="%(asctime)s "
                           "%(filename)s [line:%(lineno)d] "
                           "%(levelname)s "
                           "%(message)s",
                    datefmt="%Y-%M-%d %H:%M:%S"
                    )
linkedin_url_prefix = "https://www.linkedin.com/in/"


def scrape_person(user_id, overwrite=False, base_dir=""):
    target_url = f"{linkedin_url_prefix}{user_id}/"
    file_name = f"{base_dir}{urllib.parse.unquote(user_id)}.json"
    file_path = Path(file_name)
    if (not overwrite) and file_path.exists():
        logging.info(f"skip scrape {file_name}")
        return 0
    else:
        logging.info(f"start scrape {target_url}")
        person = Person(target_url, driver=driver, close_on_complete=False)
        with open(file_name, 'w', encoding='utf-8') as fjson:
            fjson.write(json.dumps(person.to_json(), ensure_ascii=False, ))
        logging.info(f"finish scrape {target_url}")
        return 1


def scrape_connections(file_path):
    user_ids = set()
    driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
    _ = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "mn-connections"))
    )
    connections = driver.find_element(By.CLASS_NAME, "mn-connections")
    if connections is not None:
        has_more = True

        while has_more:
            try:
                more_connections = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "scaffold-finite-scroll__load-button"))
                )
                driver.execute_script("arguments[0].click();", more_connections)
            except:
                has_more = False

            for conn in connections.find_elements_by_class_name("mn-connection-card"):
                anchor = conn.find_element_by_class_name("mn-connection-card__link")
                user_id = anchor.get_attribute("href")[len(linkedin_url_prefix):-1]
                user_ids.add(user_id)
    fconns = open(file_path, 'w', encoding='utf-8')
    for user_id in user_ids:
        fconns.write(user_id + "\n")
    fconns.close()


driver = webdriver.Chrome("./chromedriver")

email = os.getenv("LINKEDIN_USER")
password = os.getenv("LINKEDIN_PASSWORD")
actions.login(driver, email, password)  # if email and password isnt given, it'll prompt in terminal

# scrape_connections("z:\\connections.txt")

user_ids = []
with open("z:\\tmp\\connections.txt", 'r', encoding='utf-8') as fconns:
    for line in fconns:
        user_ids.append(line.strip('\n'))
fconns.close()

done = 1
limit = 5
overwrite = False
base_dir = "z:\\tmp\\"
for user_id in user_ids:
    if done <= limit:
        done += scrape_person(user_id=user_id, overwrite=overwrite, base_dir=base_dir)
    else:
        break

driver.quit()
