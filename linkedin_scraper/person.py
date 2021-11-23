from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .objects import Experience, Education, Scraper, Interest, Accomplishment, Contact
import os
from linkedin_scraper import selectors


def is_element_present(element, by, value) -> bool:
    try:
        return len(element.find_elements(by, value)) > 0
    except:
        return False


class Person(Scraper):
    __TOP_CARD = "pv-top-card"
    __WAIT_FOR_ELEMENT_TIMEOUT = 5
    __WAIT_FOR_SEARCH_TIMEOUT = 5

    def __init__(
            self,
            linkedin_url=None,
            name=None,
            about=None,
            experiences=None,
            educations=None,
            interests=None,
            accomplishments=None,
            company=None,
            job_title=None,
            location=None,
            connections=None,
            contacts=None,
            driver=None,
            get=True,
            scrape=True,
            close_on_complete=True,
    ):
        self.linkedin_url = linkedin_url
        self.name = name
        self.about = about or []
        self.experiences = experiences or []
        self.educations = educations or []
        self.interests = interests or []
        self.accomplishments = accomplishments or []
        self.also_viewed_urls = []
        self.connections = connections or []
        self.job_title = job_title
        self.location = location
        self.contacts = contacts or {}

        if driver is None:
            try:
                if os.getenv("CHROMEDRIVER") is None:
                    driver_path = os.path.join(
                        os.path.dirname(__file__), "drivers/chromedriver"
                    )
                else:
                    driver_path = os.getenv("CHROMEDRIVER")

                driver = webdriver.Chrome(driver_path)
            except:
                driver = webdriver.Chrome()

        if get:
            driver.get(linkedin_url)

        self.driver = driver

        if scrape:
            self.scrape(close_on_complete)

    def add_contacts(self, contacts):
        self.contacts = contacts

    def add_connection(self, connection):
        self.connections.append(connection)

    def add_job_title(self, job_title):
        self.job_title = job_title

    def add_about(self, about):
        self.about = about

    def add_experience(self, experience):
        self.experiences.append(experience)

    def add_education(self, education):
        self.educations.append(education)

    def add_interest(self, interest):
        self.interests.append(interest)

    def add_accomplishment(self, accomplishment):
        self.accomplishments.append(accomplishment)

    def add_location(self, location):
        self.location = location

    def scrape(self, close_on_complete=True):
        if self.is_signed_in():
            self.scrape_logged_in(close_on_complete=close_on_complete)
        else:
            print("you are not logged in!")
            x = input("please verify the capcha then press any key to continue...")
            self.scrape_not_logged_in(close_on_complete=close_on_complete)

    def _click_see_more_by_class_name(self, class_name):
        try:
            _ = WebDriverWait(self.driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            div = self.driver.find_element(By.CLASS_NAME, class_name)
            div.find_element_by_tag_name("button").click()
        except Exception as e:
            pass

    def _get_text_excluding_children(self, element):
        return self.driver.execute_script("""
        var ret = "";
        var parent = arguments[0];
        if (!parent)
            return ret;
        var child = parent.firstChild;
        while(child) {
            if (child.nodeType === Node.TEXT_NODE)
                ret += child.textContent;
            else if (child.nodeType === Node.ELEMENT_NODE && child.nodeName === 'BR')
                ret += '\\n'
            child = child.nextSibling;
        }
        return ret;
        """, element)

    def _try_get_text_from_element(self, root, selector):
        if is_element_present(root, **selector):
            return root.find_element(**selector).text.strip()
        else:
            return ""

    def scrape_logged_in(self, close_on_complete=True):
        driver = self.driver
        duration = None

        root = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
            EC.presence_of_element_located(
                (
                    By.CLASS_NAME,
                    self.__TOP_CARD,
                )
            )
        )

        self.name = root.find_element_by_class_name(selectors.NAME).text.strip()

        # get about
        try:
            see_more = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'inline-show-more-text__button')]",
                    )
                )
            )
            driver.execute_script("arguments[0].click();", see_more)

            about = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//section[contains(@class, 'pv-about-section')]/div",
                    )
                )
            )
        except:
            about = None
        if about:
            self.add_about(about.text.strip())

        # get contacts
        try:
            open_contracts = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'pv-text-details__left-panel')][2]//a[1]",
                    )
                )
            )
            driver.execute_script("arguments[0].click();", open_contracts)

            # -> get ims
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        selectors.CONTACT_IMS['by'],
                        selectors.CONTACT_IMS['value']
                    )
                )
            )
            ims_spans = driver.find_elements(**selectors.CONTACT_IMS) or []
            ims_key = []
            ims_value = []
            for ims_pos in range(len(ims_spans)):
                if ims_pos % 2 == 0:
                    ims_value.append(ims_spans[ims_pos].text.strip())
                else:
                    ims_key.append(ims_spans[ims_pos].text.strip().replace("(", "").replace(")", ""))
            contacts = dict(zip(ims_key, ims_value))

            # -> get email
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        selectors.CONTACT_EMAIL['by'],
                        selectors.CONTACT_EMAIL['value']
                    )
                )
            )
            contact_email = self._try_get_text_from_element(driver, selectors.CONTACT_EMAIL)
            if contact_email:
                contacts["email"] = contact_email

            close_contracts = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[@data-test-modal-close-btn]",
                    )
                )
            )
            driver.execute_script("arguments[0].click();", close_contracts)
        except:
            contacts = {}
        self.add_contacts(contacts)

        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/2));"
        )

        # get experience
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight*3/5));"
        )

        # -> Click SEE MORE
        self._click_see_more_by_class_name("pv-experience-section__see-more")

        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "experience-section"))
            )
            exp = driver.find_element(By.ID, "experience-section")
        except:
            exp = None

        if exp is not None:
            for position in exp.find_elements_by_class_name("pv-position-entity"):

                roles_group = position.find_elements(**selectors.MULTI_ROLES)

                if roles_group:
                    # more than one roles in same company
                    company = self._try_get_text_from_element(position, selectors.COMPANY_WITH_MULTI_ROLES)

                    for role_item in roles_group:
                        position_title = self._try_get_text_from_element(role_item, selectors.POSITION_WITH_MULTI_ROLES)

                        times = self._try_get_text_from_element(role_item, selectors.TIMES)

                        if times:
                            from_date = " ".join(times.split(" ")[:2])
                            to_date = " ".join(times.split(" ")[3:])
                        else:
                            from_date = ""
                            to_date = ""

                        duration = self._try_get_text_from_element(role_item, selectors.DURATION)

                        location = self._try_get_text_from_element(role_item, selectors.LOCATION)

                        if is_element_present(role_item, **selectors.DESCRIPTION):
                            description = (
                                self._get_text_excluding_children(
                                    element=role_item.find_element(**selectors.DESCRIPTION)))
                        else:
                            description = ""

                        experience = Experience(
                            position_title=position_title,
                            from_date=from_date,
                            to_date=to_date,
                            duration=duration,
                            location=location,
                            description=description
                        )
                        experience.institution_name = company
                        self.add_experience(experience)
                else:
                    position_title = self._try_get_text_from_element(position, selectors.POSITION_WITH_MULTI_ROLES)

                    company = self._try_get_text_from_element(position, selectors.COMPANY)

                    times = self._try_get_text_from_element(position, selectors.TIMES)

                    if times:
                        from_date = " ".join(times.split(" ")[:2])
                        to_date = " ".join(times.split(" ")[3:])
                    else:
                        from_date = ""
                        to_date = ""

                    duration = self._try_get_text_from_element(position, selectors.DURATION)

                    location = self._try_get_text_from_element(position, selectors.LOCATION)

                    if is_element_present(position, **selectors.DESCRIPTION):
                        description = (
                            self._get_text_excluding_children(
                                element=position.find_element(**selectors.DESCRIPTION)))
                    else:
                        description = ""

                    experience = Experience(
                        position_title=position_title,
                        from_date=from_date,
                        to_date=to_date,
                        duration=duration,
                        location=location,
                        description=description
                    )
                    experience.institution_name = company
                    self.add_experience(experience)

        # get job title
        job_title = driver.find_element(**selectors.JOB_TITLE_CURRENT).text.strip()
        self.add_job_title(job_title)

        # get location
        location = driver.find_element(**selectors.LOCATION_CURRENT).text.strip()
        self.add_location(location)

        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get education
        # -> Click SEE MORE
        self._click_see_more_by_class_name("pv-education-section__see-more")
        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "education-section"))
            )
            edu = driver.find_element(By.ID, "education-section")
        except:
            edu = None
        if edu:
            for school in edu.find_elements_by_class_name(
                    "pv-profile-section__list-item"
            ):
                university = school.find_element_by_class_name(
                    "pv-entity__school-name"
                ).text.strip()

                try:
                    degree = (
                        school.find_element_by_class_name("pv-entity__degree-name")
                            .find_elements_by_tag_name("span")[1]
                            .text.strip()
                    )
                    times = (
                        school.find_element_by_class_name("pv-entity__dates")
                            .find_elements_by_tag_name("span")[1]
                            .text.strip()
                    )
                    from_date, to_date = (times.split(" ")[0], times.split(" ")[2])
                except:
                    degree = None
                    from_date, to_date = (None, None)

                if is_element_present(school, **selectors.DESCRIPTION):
                    description = (
                        self._get_text_excluding_children(
                            element=school.find_element(**selectors.DESCRIPTION)))
                else:
                    description = ""
                education = Education(
                    from_date=from_date, to_date=to_date, degree=degree,
                    description=description
                )
                education.institution_name = university
                self.add_education(education)

        # get interest
        try:

        # get connections
        goto_connections = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                    "//*[contains(@class, 'pv-top-card--list')]//a",
                )
            )
        )
        driver.execute_script("arguments[0].click();", goto_connections)

        while True:
            search_results = WebDriverWait(driver, self.__WAIT_FOR_SEARCH_TIMEOUT).until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH,
                        "//div[contains(@class, 'entity-result__content')]",
                    )
                )
            )

            for result_item in search_results:
                connection_name = self._try_get_text_from_element(result_item, selectors.CONNECTION_NAME)
                connection_occupation = self._try_get_text_from_element(result_item, selectors.CONNECTION_OCCUPATION)
                url = result_item.find_element(**selectors.CONNECTION_URL).get_attribute('href')
                connection_url = url[:url.rfind('?')]
                connection_location = self._try_get_text_from_element(result_item, selectors.CONNECTION_LOCATION)
                self.add_connection(Contact(name=connection_name, occupation=connection_occupation, url=connection_url,
                                            location=connection_location))

            driver.execute_script("var q=document.documentElement.scrollTop=10000")
            driver.implicitly_wait(2)
            goto_next = driver.find_element(By.XPATH, "//button[contains(@class, 'artdeco-pagination__button--next')]")
            if goto_next.get_attribute('disabled') != 'true':
                driver.execute_script("arguments[0].click();", goto_next)
            else:
                break

        # try:
        #     driver.get("https://www.linkedin.com/mynetwork/invite-connect/connections/")
        #     _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
        #         EC.presence_of_element_located((By.CLASS_NAME, "mn-connections"))
        #     )
        #     connections = driver.find_element(By.CLASS_NAME, "mn-connections")
        #     if connections is not None:
        #         for conn in connections.find_elements_by_class_name("mn-connection-card"):
        #             anchor = conn.find_element_by_class_name("mn-connection-card__link")
        #             url = anchor.get_attribute("href")
        #             name = conn.find_element_by_class_name("mn-connection-card__details").find_element_by_class_name(
        #                 "mn-connection-card__name").text.strip()
        #             occupation = conn.find_element_by_class_name(
        #                 "mn-connection-card__details").find_element_by_class_name(
        #                 "mn-connection-card__occupation").text.strip()
        #
        #             contact = Contact(name=name, occupation=occupation, url=url)
        #             self.add_contact(contact)
        # except:
        #     connections = None



        if close_on_complete:
            driver.quit()

    def scrape_not_logged_in(self, close_on_complete=True, retry_limit=10):
        driver = self.driver
        retry_times = 0
        while self.is_signed_in() and retry_times <= retry_limit:
            page = driver.get(self.linkedin_url)
            retry_times = retry_times + 1

        # get name
        self.name = driver.find_element(By.CLASS_NAME,
                                        "top-card-layout__title"
                                        ).text.strip()

        # get experience
        try:
            _ = WebDriverWait(driver, self.__WAIT_FOR_ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "experience"))
            )
            exp = driver.find_element(By.CLASS_NAME, "experience")
        except:
            exp = None

        if exp is not None:
            for position in exp.find_elements_by_class_name(
                    "experience-item__contents"
            ):
                position_title = position.find_element_by_class_name(
                    "experience-item__title"
                ).text.strip()
                company = position.find_element_by_class_name(
                    "experience-item__subtitle"
                ).text.strip()

                try:
                    times = position.find_element_by_class_name(
                        "experience-item__duration"
                    )
                    from_date = times.find_element_by_class_name(
                        "date-range__start-date"
                    ).text.strip()
                    try:
                        to_date = times.find_element_by_class_name(
                            "date-range__end-date"
                        ).text.strip()
                    except:
                        to_date = "Present"
                    duration = position.find_element_by_class_name(
                        "date-range__duration"
                    ).text.strip()
                    location = position.find_element_by_class_name(
                        "experience-item__location"
                    ).text.strip()
                except:
                    from_date, to_date, duration, location = (None, None, None, None)

                experience = Experience(
                    position_title=position_title,
                    from_date=from_date,
                    to_date=to_date,
                    duration=duration,
                    location=location,
                )
                experience.institution_name = company
                self.add_experience(experience)
        driver.execute_script(
            "window.scrollTo(0, Math.ceil(document.body.scrollHeight/1.5));"
        )

        # get education
        edu = driver.find_element(By.CLASS_NAME, "education__list")
        for school in edu.find_elements_by_class_name("result-card"):
            university = school.find_element_by_class_name(
                "result-card__title"
            ).text.strip()
            degree = school.find_element_by_class_name(
                "education__item--degree-info"
            ).text.strip()
            try:
                times = school.find_element_by_class_name("date-range")
                from_date = times.find_element_by_class_name(
                    "date-range__start-date"
                ).text.strip()
                to_date = times.find_element_by_class_name(
                    "date-range__end-date"
                ).text.strip()
            except:
                from_date, to_date = (None, None)
            education = Education(from_date=from_date, to_date=to_date, degree=degree)

            education.institution_name = university
            self.add_education(education)

        if close_on_complete:
            driver.close()

    def to_json(self):
        json = {}
        json["name"] = self.name
        json["about"] = self.about
        json["job_title"] = self.job_title
        json["location"] = self.location
        json["contacts"] = self.contacts
        json["experiences"] = []
        json["educations"] = []
        json["connections"] = []

        for experience in self.experiences:
            exp = {}
            exp["company"] = experience.institution_name
            exp["position_title"] = experience.position_title
            exp["from_date"] = experience.from_date
            exp["to_date"] = experience.to_date
            exp["duration"] = experience.duration
            exp["location"] = experience.location
            exp["description"] = experience.description
            json["experiences"].append(exp)

        for education in self.educations:
            edu = {}
            edu["institution_name"] = education.institution_name
            edu["degree"] = education.degree
            edu["from_date"] = education.from_date
            edu["to_date"] = education.to_date
            json["educations"].append(edu)

        for connection in self.connections:
            con = {}
            con["name"] = connection.name
            con["occupation"] = connection.occupation
            con["url"] = connection.url
            con["location"] = connection.location
            json["connections"].append(con)

        return json

    @property
    def company(self):
        if self.experiences:
            return (
                self.experiences[0].institution_name
                if self.experiences[0].institution_name
                else None
            )
        else:
            return None

    def __repr__(self):
        return "{name}\n\nAbout\n{about}\n\nExperience\n{exp}\n\nEducation\n{edu}\n\nInterest\n{int}\n\nAccomplishments\n{acc}\n\nContacts\n{conn}".format(
            name=self.name,
            about=self.about,
            exp=self.experiences,
            edu=self.educations,
            int=self.interests,
            acc=self.accomplishments,
            conn=self.contacts,
        )
