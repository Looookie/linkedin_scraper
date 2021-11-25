import os
import json
import urllib.parse
import logging
import pickle
from pathlib import Path
from linkedin_scraper import Person, actions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from multiprocessing import Queue
from threading import Thread

from samples.atomic_counter import AtomicCounter

log_file = open("z:\\scrape.log", encoding="utf-8", mode="a")
logging.basicConfig(level=logging.INFO,
                    stream=log_file,
                    format="%(asctime)s "
                           "%(filename)s [line:%(lineno)d] "
                           "%(levelname)s "
                           "%(message)s",
                    datefmt="%Y-%M-%d %H:%M:%S"
                    )


class WorkerConfig:
    limit: int = 1
    overwrite: bool = False
    base_dir: str = None

    def __init__(
            self,
            limit=1,
            overwrite=False,
            base_dir=""
    ):
        self.limit = limit
        self.overwrite = overwrite
        self.base_dir = base_dir


LINKEDIN_URL_PREFIX = "https://www.linkedin.com/in/"
STOP_FLAG = "==STOP=="
config = WorkerConfig(base_dir="Z:\\tmp\\", limit=50)
concurrency = 4


# save cookies
def save_cookies(path):
    # login
    email = os.getenv("LINKEDIN_USER")
    password = os.getenv("LINKEDIN_PASSWORD")
    driver = webdriver.Chrome(options=options, executable_path="./chromedriver")
    actions.login(driver, email, password)  # if email and password isnt given, it'll prompt in terminal

    # do login steps, so cookies can be set
    pickle.dump(driver.get_cookies(), open(path, "wb"))
    driver.quit()


# load cookies
def load_cookies(driver, path):
    driver.get("https://www.linkedin.com/")
    cookies = pickle.load(open(path, "rb"))
    for cookie in cookies:
        driver.add_cookie(cookie)


def scrape_connections(driver, file_path):
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
                user_id = anchor.get_attribute("href")[len(LINKEDIN_URL_PREFIX):-1]
                user_ids.add(user_id)
    fconns = open(file_path, 'w', encoding='utf-8')
    for user_id in user_ids:
        fconns.write(user_id + "\n")
    fconns.close()


# scrape_connections("z:\\connections.txt")

# Prepare data
selenium_data = []
with open("z:\\tmp\\connections.txt", 'r', encoding='utf-8') as fconns:
    for (num, line) in enumerate(fconns):
        selenium_data.append(line.strip('\n'))
selenium_data.append(STOP_FLAG)

worker_ids = list(range(concurrency))
selenium_data_queue = Queue()
worker_queue = Queue()
selenium_workers = {}

# Prepare workers
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("detach", True)
options.add_experimental_option('prefs', {'credentials_enable_service': False,
                                          'profile': {'password_manager_enabled': False}})
for worker_id in worker_ids:
    selenium_workers[worker_id] = webdriver.Chrome(options=options, executable_path="./chromedriver")
    worker_queue.put(worker_id)

cookie_path = "z:\\cookie.pkl"

# transfer cookies
save_cookies(cookie_path)
for wid in worker_ids:
    load_cookies(selenium_workers[wid], cookie_path)


def selenium_task(worker, user_id, worker_id, worker_config):
    """
    This is a demonstration selenium function that takes a worker and data and then does something with the worker and
    data.
    TODO: change the below code to be whatever it is you want your worker to do e.g. scrape webpages or run browser tests
    :param worker: A selenium web worker NOT a worker ID
    :type worker: webdriver.XXX
    :param user_id: Id of user
    :param worker_id: Id of worker
    :param worker_config: WorkerConfig
    """
    target_url = f"{LINKEDIN_URL_PREFIX}{user_id}/"
    file_name = f"{worker_config.base_dir}{urllib.parse.unquote(user_id)}.json"
    file_path = Path(file_name)
    if (not worker_config.overwrite) and file_path.exists():
        logging.debug(f"worker-{worker_id} skip scrape {target_url}")
        return 0
    else:
        logging.info(f"worker-{worker_id} start scrape {target_url}")
        try:
            person = Person(target_url, driver=worker, close_on_complete=False)
            with open(file_name, 'w', encoding='utf-8') as fjson:
                fjson.write(json.dumps(person.to_json(), ensure_ascii=False, ))
            logging.info(f"worker-{worker_id} finish scrape {target_url} -> {file_path}")
            return 1
        except:
            logging.exception(f"worker-{worker_id} fail to scrape {target_url}")
            return 0


def selenium_queue_listener(data_queue, worker_id_queue, listener_id, task_counter, worker_config):
    """
    Monitor a data queue and assign new pieces of data to any available web workers to action
    :param data_queue: The python FIFO queue containing the data to run on the web worker
    :type data_queue: Queue
    :param worker_id_queue: The queue that holds the IDs of any idle workers
    :type worker_id_queue: Queue
    :param listener_id:
    :param worker_config: WorkerConfig
    :param task_counter: AtomicCounter
    """
    logging.info("Selenium func worker started")
    while True:
        if task_counter.value >= worker_config.limit:
            logging.info(f"listener-{listener_id} close")
            break

        current_data = data_queue.get()
        if current_data == STOP_FLAG:
            # If a stop is encountered then kill the current worker and put the stop back onto the queue
            # to poison other workers listening on the queue
            logging.warning("STOP encountered, killing worker thread")
            data_queue.put(current_data)
            break
        # Get the ID of any currently free workers from the worker queue
        worker_id = worker_id_queue.get()
        worker = selenium_workers[worker_id]
        # Assign current worker and current data to your selenium function
        done = selenium_task(worker, current_data, worker_id, worker_config)
        # Put the worker back into the worker queue as  it has completed it's task
        worker_queue.put(worker_id)
        if done > 0:
            task_counter.inc()
            logging.info(f"listner-{listener_id} has completed task, total {task_counter.value} done.")
    return


counter = AtomicCounter()
# Create one new queue listener thread per selenium worker and start them
logging.info("Starting selenium background processes")
selenium_processes = [Thread(target=selenium_queue_listener,
                             args=(selenium_data_queue, worker_queue, wid, counter, config)) for wid in worker_ids]
for p in selenium_processes:
    p.daemon = True
    p.start()

# Add each item of data to the data queue, this could be done over time so long as the selenium queue listening
# processes are still running
logging.info("Adding data to data queue")
for d in selenium_data:
    selenium_data_queue.put(d)

# Wait for all selenium queue listening processes to complete, this happens when the queue listener returns
logging.info("Waiting for Queue listener threads to complete")
for p in selenium_processes:
    p.join()

# Quit all the web workers elegantly in the background
logging.info("Tearing down web workers")
for b in selenium_workers.values():
    b.quit()

exit()
