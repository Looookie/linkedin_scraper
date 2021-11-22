import os
from linkedin_scraper import Person, actions
from selenium import webdriver
driver = webdriver.Chrome("./chromedriver")

email = os.getenv("LINKEDIN_USER")
password = os.getenv("LINKEDIN_PASSWORD")
actions.login(driver, email, password) # if email and password isnt given, it'll prompt in terminal
person = Person("https://www.linkedin.com/in/andre-iguodala-65b48ab5", driver=driver)
print("Person: " + person.name)
print("Person About: ")
print(person.about)
print("Person Experiences: ")
for experience in person.experiences:
    print(f"--: {experience.institution_name} - {experience.position_title}")
    print(
        f"from {experience.from_date} to {experience.to_date} ({experience.duration})")
    print(
        f"{experience.description}")
