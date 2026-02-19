# Description: This script scrapes data from the Tel Aviv Stock Exchange (TASE) website.
# It downloads the following data:
# 1. Index components
# 2. Currency exchange rates
# 3. Company finance reports
# The data is saved in the 'data' folder in the current working directory.
# The script uses Selenium to automate the process of downloading the data.
# The script requires the user to log in to the TASE website manually (doing so with a Google account might not work with Selenium).
# Author: Marc Berneman
import json

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from pathlib import Path
import pandas as pd
import time
from tqdm import tqdm
import datetime

sleep_time = 1.5
sleep = lambda : time.sleep(sleep_time)

download_dir = Path.cwd() / 'data'  / datetime.date.today().strftime('%d%m%Y')
download_dir.mkdir(exist_ok=True)

options = webdriver.ChromeOptions()
prefs = {"download.default_directory": str(download_dir)}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)
driver.maximize_window()
wait = WebDriverWait(driver, 10)

url = 'https://www.tase.co.il/en'
driver.get(url)
input('Press Enter after you log in...')

def get_company_id(_driver, _security_id):
    # keep a file in json format with the mapping of security_id to company_id
    # if the file doesn't exist or if the security_id is not in the file, ask the user to input the company_id
    # then save the mapping to the file
    # if the file exists and the security_id is in the file, return the company_id
    _file = download_dir.parent / 'companyids.json'
    _security_id = int(_security_id)
    if not _file.exists():
        company_id = input(f'Please enter the company ID for security ID {_security_id}: ')
        dictionary = {_security_id: company_id}
        with open(_file, 'w') as f:
            json.dump(dictionary, f)
        return company_id
    else:
        with open(_file, 'r') as f:
            dictionary = json.load(f)
        if str(_security_id) in dictionary:
            return dictionary[str(_security_id)]
        else:
            url = f'https://market.tase.co.il/en/market_data/security/{security_id}/major_data'
            driver.get(url)
            company_id = input(f'Please enter the company ID for security ID {_security_id}: ')
            dictionary[_security_id] = company_id
            with open(_file, 'w') as f:
                json.dump(dictionary, f)
            return company_id


def get_index_components():
    if not (download_dir / 'indexcomponents.csv').exists():
        url = 'https://market.tase.co.il/en/market_data/index/142/components/index_weight'
        driver.get(url)

        sleep()

        download_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Download Data']"))
        )
        download_button.click()

        sleep()

        csv_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@aria-label='Choose File Type']//a[normalize-space()='CSV']"))
        )
        csv_option.click()

        sleep()

def get_company_finance_report(security_id):
    file_download = download_dir / 'financial-report.csv'
    file_download.unlink(missing_ok=True)
    file = download_dir / f'{symbol}FinanceReport.csv'
    if not file.exists():
        company_id = get_company_id(driver, security_id)
        url = f'https://maya.tase.co.il/en/companies/{company_id}/financial-reports'
        driver.get(url)

        # Locate the h2
        heading = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//h2[contains(text(),'Financial Statements – Key Data')]")
            )
        )

        # Get the text
        heading_text = heading.text

        # Check currency
        if "USD" in heading_text:
            currency = "USD"
        elif "NIS" in heading_text:
            currency = "NIS"
        else:
            raise ValueError(f"Currency not found in heading text: {heading_text}")
        with open(download_dir / 'currency.csv', 'a') as f:
            f.write(f"{symbol},{currency}\n")

        sleep()

        download_btn = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//button[contains(@class,'ma-tooltip')][.//span[@aria-label='Download Data']]"
            ))
        )
        ActionChains(driver).move_to_element(download_btn).pause(0.3).click().perform()

        sleep()

        file_download.rename(file)


def get_currency_exchange():
    if not (download_dir / 'dailyreviewforeignexchange.csv').exists():
        url = 'https://market.tase.co.il/en/market_data/daily-review/exchange_rates'
        driver.get(url)

        sleep()

        download_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Download Data']"))
        )
        download_button.click()

        sleep()

        csv_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//ul[@aria-label='Choose File Type']//a[normalize-space()='CSV']"))
        )
        csv_option.click()

        sleep()


while True:
    try:
        get_index_components()
        get_currency_exchange()

        file = download_dir / 'indexcomponents.csv'
        df = pd.read_csv(file, header=2)
        df.columns = df.columns.str.strip()  # remove space from column names
        df = df[['Symbol', 'Security No']]

        for i in tqdm(range(len(df))):
            symbol = df['Symbol'].iloc[i]
            security_id = df['Security No'].iloc[i]

            get_company_finance_report(security_id)
    except TimeoutException:
        input('\nTimeoutException: please fix the issue and press Enter. Bringing the window into view might help...')
        continue
    break

driver.quit()