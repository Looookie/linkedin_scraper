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
print("Person Job Title: ")
print(person.job_title)
print("Person Location: ")
print(person.location)
print("Person Experiences: ")
for experience in person.experiences:
    print(f"--: {experience.institution_name} - {experience.position_title}")
    print(
        f"from {experience.from_date} to {experience.to_date} ({experience.duration}) at {experience.location}")
    print(
        f"{experience.description}")

for education in person.educations:
    print(f"--: {education.institution_name} - {education.degree}")
    print(
        f"from {education.from_date} to {education.to_date}")
    print(
        f"{education.description}")

for contact in person.contacts:
    print(f"--: {contact.name} - {contact.occupation} - {contact.url}")