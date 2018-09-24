import flickrapi, json
from datetime import datetime
from mongoconnector import MongoConnector
from mlstripper import MLStripper
from tqdm import tqdm


class FlickrScraper:
    PAGE_LIMIT = 100
    PAGES = 10
    extras = 'description, date_upload, owner_name, tags, views, media, ' \
             'path_alias, url_c, url_l, url_o, count_faves'

    def __init__(self):
        pass

    def establish_connection(self):
        with open("credentials.json") as json_file:
            credentials = json.load(json_file)

        flickr = flickrapi.FlickrAPI(credentials["flickr_key"], credentials["flickr_secret"], format='parsed-json')
        return flickr

    def scrape_hashtag(self, flickr, tag):
        print('Scraping on flickr')
        for i in range(1, self.PAGES + 1):
            print('\nPage ' + str(i))
            photos = flickr.photos.search(text=tag.replace('#', ''), per_page=self.PAGE_LIMIT + 1, page=i,
                                      extras=self.extras, sort='interestingness-desc')
            posts = list()
            for photo in tqdm(photos['photos']['photo']):
                comments_full = flickr.photos.comments.getList(photo_id=photo['id'])
                post = dict()
                url = 'https://www.flickr.com/photos/' + photo['owner'] + '/' + photo['id']
                post['url'] = url
                post['source'] = 'www.flickr.com'
                post['title'] = photo['title']
                post['user_name'] = photo['ownername']
                image_url = self.get_biggest_image_url(photo)
                if not image_url:
                    continue
                post['image_url'] = image_url
                post['description'] = self.strip_tags(photo['description']['_content'])
                post['hashtags'] = photo['tags'].split()
                post['likes'] = photo['count_faves']
                post['date'] = datetime.utcfromtimestamp(int(photo['dateupload'])).strftime('%Y-%m-%d %H:%M:%S')
                comments = list()
                try:
                    for c in comments_full['comments']['comment']:
                        res = dict()
                        res['commenter'] = c['authorname']
                        res['comment'] = c['_content']
                        comments.append(res)
                except KeyError:
                    comments.clear()
                post['comments'] = comments
                posts.append(post)
            MongoConnector.save_to_db(posts, tag.replace('#', ''))

    def get_biggest_image_url(self, photo):
        try:
            return photo['url_o']
        except KeyError:
            try:
                return photo['url_l']
            except KeyError:
                try:
                    return photo['url_c']
                except KeyError:
                    return None

    def strip_tags(self, html):
        s = MLStripper()
        s.feed(html)
        return s.get_data()


if __name__ == '__main__':
    flickr_scraper = FlickrScraper()
    flickr = flickr_scraper.establish_connection()
    flickr_scraper.scrape_hashtag(flickr, 'sport')
