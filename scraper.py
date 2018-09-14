from selenium.webdriver import ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time


class Scraper:

    def __init__(self):
        opts = ChromeOptions()
        opts.add_experimental_option("detach", True)
        opts.add_argument("start-maximized")
        opts.add_argument("disable-infobars")

        driver = webdriver.Chrome('./chromedriver/chromedriver', chrome_options=opts)
        driver.get('https://www.instagram.com')

        self.login(driver)
        posts = self.get_posts_by_tag(driver, "#picoftheday", 100)
        print('%s' % posts)

    def login(self, driver):
        element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="react-root"]/section/main/article/div[2]/div[2]/p/a')))
        element.click()

        time.sleep(1)

        with open("credentials.json", "r") as json_file:
            credentials = json.load(json_file)

        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="username"]'))).send_keys(credentials["user"])
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="password"]'))).send_keys(credentials["password"])
        button = WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'button[class="_5f5mN       jIbKX KUBKM      yZn4P   "]')))
        if button.is_enabled():
            button.click()

    def get_posts_by_tag(self, driver, tag, number):
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[placeholder="Cerca"]'))).send_keys(tag)
        send = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[class="Ap253"]')))
        send.click()

        popular_posts = WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located(
            (By.XPATH, '//*[@id="react-root"]/section/main/article/div[1]/div/div/div/div/a')))

        posts = set()
        for el in popular_posts:
            posts.add(el.get_attribute("href"))
        while len(posts) <= number - len(popular_posts):
            new_posts = WebDriverWait(driver, 5).until(EC.visibility_of_all_elements_located(
                (By.XPATH, '//*[@id="react-root"]/section/main/article/div[2]/div/div/div/a')))
            for el in new_posts:
                posts.add(el.get_attribute("href"))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        return posts


if __name__ == '__main__':
    Scraper()
