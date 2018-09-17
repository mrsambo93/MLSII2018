from selenium.webdriver import ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import json
import time
import os


class Scraper:
    OUTPUT_DIR = "posts"

    def __init__(self):
        if not os.path.isdir(self.OUTPUT_DIR):
            os.mkdir(self.OUTPUT_DIR)
        opts = ChromeOptions()
        opts.add_experimental_option('detach', True)
        prefs = {'profile.managed_default_content_settings.images': 2, 'disk-cache-size': 4096}
        opts.add_experimental_option('prefs', prefs)
        opts.add_argument('--disable-popup-blocking')
        opts.add_argument('start-maximized')
        opts.add_argument('disable-infobars')

        driver = webdriver.Chrome('./chromedriver/chromedriver', chrome_options=opts)
        driver.get('https://www.instagram.com')

        self.login(driver)
        posts_link = self.get_posts_by_tag(driver, "#picoftheday", 100)
        print('%s' % posts_link)

        posts = self.scrape_posts(driver, posts_link)

        self.save_to_file(posts, "#picoftheday")

        driver.quit()

    def login(self, driver):
        element = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.XPATH, '//*[@id="react-root"]/section/main/article/div[2]/div[2]/p/a')))
        element.click()

        time.sleep(1)

        with open("credentials.json", "r") as json_file:
            credentials = json.load(json_file)

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="username"]'))).send_keys(credentials["user"])
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="password"]'))).send_keys(credentials["password"])
        button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'button[class="_5f5mN       jIbKX KUBKM      yZn4P   "]')))
        if button.is_enabled():
            button.click()

    def get_posts_by_tag(self, driver, tag, number):
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'button[class="chBAG"]'))).click()
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[placeholder="Cerca"]'))).send_keys(tag)
        send = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'span[class="Ap253"]')))
        send.click()

        popular_posts = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located(
            (By.XPATH, '//*[@id="react-root"]/section/main/article/div[1]/div/div/div/div/a')))

        posts = set()
        for el in popular_posts:
            posts.add(el.get_attribute("href"))
        while len(posts) <= number - len(popular_posts):
            new_posts = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located(
                (By.XPATH, '//*[@id="react-root"]/section/main/article/div[2]/div/div/div/a')))
            for el in new_posts:
                posts.add(el.get_attribute('href'))
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        posts_list = list()
        for elem in posts:
            posts_list.append(elem)
        return posts_list

    def scrape_posts(self, driver, posts_link):
        scraped = list()
        page_counter = 0
        for post_link in posts_link:
            try:
                if page_counter == 10:
                    page_counter = 0
                    time.sleep(2)
                page_counter += 1
                driver.get(post_link)
                post = dict()
                post["url"] = post_link
                user_name = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'a[class="FPmhX notranslate TlrDj"]'))).get_attribute('title')
                description = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.XPATH,
                        '//*[@id="react-root"]/section/main/div/div/article/div[2]/div[1]/ul/li[1]/div/div/div/span')))\
                    .text
                hashtags = list({tag for tag in description.split() if tag.startswith('#')})
                likes_selector = self.get_likes(driver)
                likes = 0
                if likes_selector:
                    likes_text = likes_selector.text
                    likes = int(''.join(filter(str.isdigit, likes_text)))
                date = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'time[class="_1o9PC Nzb55"]'))).get_attribute('datetime')
                image_url = self.get_image_url(driver)
                if image_url:
                    post["image_url"] = image_url
                video_url = self.get_video_url(driver)
                if video_url:
                    post["video_url"] = video_url
                post["user_name"] = user_name
                post["description"] = description
                post["hashtags"] = hashtags
                post["likes"] = likes
                post["date"] = date
                post["comments"] = list()
                comments = self.get_comments(driver)
                if comments:
                    for comment in comments:
                        commenter = comment.find_element_by_css_selector('a[class="FPmhX notranslate TlrDj"]')\
                            .get_attribute('title')
                        comm_descr = comment.find_element_by_css_selector('span').text
                        post["comments"].append({
                            "commenter": commenter,
                            "comment": comm_descr
                        })
                scraped.append(post)
            except TimeoutException:
                pass
        return scraped

    def get_comments(self, driver):
        try:
            return driver.find_elements_by_css_selector('li[class="gElp9 "]')
        except NoSuchElementException:
            return None

    def get_likes(self, driver):
        try:
            return driver.find_element_by_css_selector('a[class="zV_Nj')
        except NoSuchElementException:
            return None

    def get_image_url(self, driver):
        try:
            return driver.find_element_by_css_selector('img[class="FFVAD"]').get_attribute('src')
        except NoSuchElementException:
            return None

    def get_video_url(self, driver):
        try:
            return driver.find_element_by_css_selector('video[class="tWeCl"]').get_attribute('src')
        except NoSuchElementException:
            return None

    def save_to_file(self, posts, tag):
        with open(self.OUTPUT_DIR + '/' + tag + ".json", "w") as output_file:
            json.dump(posts, output_file, indent=4)


if __name__ == '__main__':
    Scraper()
