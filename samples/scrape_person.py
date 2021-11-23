import os
import json
from linkedin_scraper import Person, actions
from selenium import webdriver
driver = webdriver.Chrome("./chromedriver")

email = os.getenv("LINKEDIN_USER")
password = os.getenv("LINKEDIN_PASSWORD")
actions.login(driver, email, password) # if email and password isnt given, it'll prompt in terminal

target = "https://www.linkedin.com/in/jackxxguo/"
person = Person(target, driver=driver)

string = "/in/"
with open(f'z:\\{target[target.rfind(string) + len(string)::].rstrip("/")}.json', 'w', encoding='utf-8') as fjson:
    fjson.write(json.dumps(person.to_json(), ensure_ascii=False, ))