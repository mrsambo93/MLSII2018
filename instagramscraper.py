from selenium.webdriver import ChromeOptions
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import json
import time
import os
from tqdm import tqdm
from mongoconnector import MongoConnector


class InstagramScraper:
    OUTPUT_DIR = "posts"
    OUTPUT_TAG_DIR = "posts/hashtags"
    OUTPUT_USER_DIR = "posts/users"
    TAG = "tag"
    USER = "user"
    COMMENTS_LIMIT = 10
    POSTS_LIMIT = 10
    credentials = dict()

    def __init__(self):
        if not os.path.isdir(self.OUTPUT_DIR):
            os.mkdir(self.OUTPUT_DIR)
        if not os.path.isdir(self.OUTPUT_TAG_DIR):
            os.mkdir(self.OUTPUT_TAG_DIR)
        if not os.path.isdir(self.OUTPUT_USER_DIR):
            os.mkdir(self.OUTPUT_USER_DIR)

        with open("credentials.json", "r") as json_file:
            self.credentials = json.load(json_file)

    def establish_connection(self):
        opts = ChromeOptions()
        opts.add_experimental_option('detach', True)
        prefs = {'profile.managed_default_content_settings.images': 2, 'disk-cache-size': 4096}
        opts.add_experimental_option('prefs', prefs)
        opts.add_argument('--disable-popup-blocking')
        # opts.add_argument("start-maximized")
        opts.add_argument('--no-proxy-server')
        opts.add_argument('headless')
        opts.add_argument('disable-infobars')

        driver = webdriver.Chrome('./chromedriver/chromedriver', chrome_options=opts)

        self.login(driver)

        return driver

    def end_connection(self, driver):
        driver.quit()

    def login(self, driver):
        driver.get("https://www.instagram.com/accounts/login/?source=auth_switcher")

        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="username"]'))).send_keys(self.credentials["user"])
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'input[name="password"]'))).send_keys(self.credentials["password"])
        button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
            (By.CSS_SELECTOR, 'button[class="_5f5mN       jIbKX KUBKM      yZn4P   "]')))
        if button.is_enabled():
            button.click()
            print("Logged in")

    def scrape_hashtag(self, driver, hashtag):
        posts_link = self.get_posts_by_tag(driver, hashtag, self.POSTS_LIMIT)
        posts = self.scrape_posts(driver, posts_link)
        self.save_to_file(posts, hashtag, self.TAG)
        MongoConnector.save_to_db(posts)

    def scrape_user(self, driver, username):
        posts_link = self.get_user_posts(driver, username, self.POSTS_LIMIT)
        posts = self.scrape_posts(driver, posts_link)
        self.save_to_file(posts, username, self.USER)
        MongoConnector.save_to_db(posts)

    def get_posts_by_tag(self, driver, tag, number):
        self.close_pop_up(driver)
        driver.get("https:/www.instagram.com/explore/" + tag)

        print("Collecting posts for " + tag)
        posts = set()
        while len(posts) <= number:
            new_posts = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located(
                (By.XPATH, '//*[@id="react-root"]/section/main/div/article/div[1]/div/div/div/a')))
            for el in new_posts:
                posts.add(el.get_attribute('href'))
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

        posts_list = list()
        for elem in posts:
            posts_list.append(elem)
        return posts_list

    def get_user_posts(self, driver, username, number):
        self.close_pop_up(driver)
        driver.get('https:/www.instagram.com/' + username)

        print("Collectiong posts for " + username)
        posts = set()
        while len(posts) <= number:
            new_posts = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located(
                (By.XPATH, '//*[@id="react-root"]/section/main/div/div[2]/article/div[1]/div/div/div/a')))
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
        print("Scraping")
        for post_link in tqdm(posts_link):
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
                hashtags = list({tag.replace('#', '') for tag in description.split() if tag.startswith('#')})
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
                post["date"] = date.replace('T', ' ').replace('.000Z', '')
                post["source"] = "www.instagram.com"
                post["comments"] = list()
                comments = self.get_comments(driver)
                if comments:
                    self.expand_comments(driver, self.COMMENTS_LIMIT)
                    comments_hashtags = set()
                    for i, comment in enumerate(comments):
                        if i == 0:
                            continue
                        commenter = comment.find_element_by_css_selector('a[class="FPmhX notranslate TlrDj"]')\
                            .get_attribute('title')
                        comm_descr = comment.find_element_by_css_selector('span').text
                        for tag in comm_descr.split():
                            if tag.startswith('#'):
                                comments_hashtags.add(tag.replace('#', ''))
                        post["comments"].append({
                            "commenter": commenter,
                            "comment": comm_descr
                        })
                    if comments_hashtags:
                        post["comments_hashtags"] = list(comments_hashtags)
                scraped.append(post)
            except TimeoutException:
                continue
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

    def expand_comments(self, driver, limit):
        try:
            i = 0
            while i < limit:
                more = WebDriverWait(driver, 1).until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'li[class="lnrre"]')))
                more.click()
                i += 1
        except TimeoutException:
            return

    def close_pop_up(self, driver):
        try:
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, 'button[class="chBAG"]'))).click()
        except TimeoutException:
            return

    def save_to_file(self, posts, name, type):
        directory = ''
        if type == self.TAG:
            directory = self.OUTPUT_TAG_DIR
        if type == self.USER:
            directory = self.OUTPUT_USER_DIR
        if not directory:
            return
        with open(directory + '/' + name + ".json", "w") as output_file:
            json.dump(posts, output_file, indent=4)


if __name__ == '__main__':
    scraper = InstagramScraper()
    driv = scraper.establish_connection()
    scraper.scrape_hashtag(driv, "#sport")
    scraper.end_connection(driv)
