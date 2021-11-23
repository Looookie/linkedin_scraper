from selenium.webdriver.common.by import By

NAME = "text-heading-xlarge"

TOP_CARD = {
    'by': By.XPATH,
    'value': "//section[contains(@class, 'pv-top-card')]"
}

MULTI_ROLES = {
    'by': By.XPATH,
    'value': ".//*[contains(@class, 'pv-entity__position-group-role-item')]/div"
}

COMPANY_WITH_MULTI_ROLES = {
    'by': By.XPATH,
    'value': ".//h3/span[2]"
}

POSITION_WITH_MULTI_ROLES = {
    'by': By.XPATH,
    'value': ".//h3/span[2]"
}

COMPANY = {
    'by': By.XPATH,
    'value': ".//h3"
}

POSITION = {
    'by': By.XPATH,
    'value': ".//p[contains(@class, 'pv-entity__secondary-title')]"
}

TIMES = {
    'by': By.XPATH,
    'value': ".//h4[contains(@class, 'pv-entity__date-range')]/span[2]"
}

DURATION = {
    'by': By.XPATH,
    'value': ".//h4/span[@class='pv-entity__bullet-item-v2']"
}

LOCATION = {
    'by': By.XPATH,
    'value': ".//h4[contains(@class, 'pv-entity__location')]/span[2]"
}

DESCRIPTION = {
    'by': By.XPATH,
    'value': ".//div[contains(@class, 'pv-entity__description')]"
}

JOB_TITLE_CURRENT = {
    'by': By.XPATH,
    'value': "//div[contains(@class, 'pv-text-details__left-panel')]/div[2]"
}

LOCATION_CURRENT = {
    'by': By.XPATH,
    'value': "//div[contains(@class, 'pv-text-details__left-panel')][2]/span[1]"
}

CONTACT_EMAIL = {
    'by': By.XPATH,
    'value': "//section[contains(@class, 'ci-email')]/div"
}

CONTACT_IMS = {
    'by': By.XPATH,
    'value': "//section[contains(@class, 'ci-ims')]//span"
}

CONNECTION_NAME = {
    'by': By.XPATH,
    'value': "(.//a[1]/span/span)[1]"
}

CONNECTION_OCCUPATION = {
    'by': By.XPATH,
    'value': ".//div[contains(@class, 'entity-result__primary-subtitle')]"
}

CONNECTION_URL = {
    'by': By.XPATH,
    'value': ".//a[1]"
}

CONNECTION_LOCATION = {
    'by': By.XPATH,
    'value': ".//div[contains(@class, 'entity-result__secondary-subtitle')]"
}
