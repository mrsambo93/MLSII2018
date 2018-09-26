from mongoconnector import MongoConnector
from instagramscraper import InstagramScraper
from flickrscraper import FlickrScraper
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import re
import nltk

nltk.download('words')
words = set(nltk.corpus.words.words())


class Recommender:

    def __init__(self):
        """MongoConnector.translate_to_english('sport')
        MongoConnector.translate_to_english('food')"""
        pass

    def get_recommendations(self, post_url):
        posts = MongoConnector.get_all_posts()
        existent = None
        post = None
        if 'instagram' in post_url:
            for post in posts:
                if self.remove_query(post['url']) == self.remove_query(post_url):
                    existent = p
                    break
            if not existent:
                instagram_scraper = InstagramScraper()
                driver = instagram_scraper.establish_connection()
                post = instagram_scraper.scrape_post(driver, post_url)
                posts.append(post)
            else:
                post = existent
        elif 'flickr' in post_url:
            for p in posts:
                if self.get_id(p['url']) == self.get_id(post_url):
                    existent = p
                    break
            if not existent:
                flickr_scraper = FlickrScraper()
                flickr = flickr_scraper.establish_connection()
                post = flickr_scraper.scrape_post(flickr, post_url)
                posts.append(post)
            else:
                post = existent
        if post:
            tfidf = TfidfVectorizer(stop_words='english')

            df = pd.DataFrame(posts)
            df['title'] = df['title'].fillna('')
            df['title'] = df['title'].apply(MongoConnector.clean_string).apply(remove_other_languages)
            df['comments_hashtags'] = df['comments_hashtags'].fillna('')
            df['comments'] = df['comments'].apply(get_comments)
            df['comments'] = df['comments'].apply(remove_from_all)
            df['description'] = df['description'].apply(MongoConnector.clean_string)
            df['description'] = df['description'].apply(remove_other_languages)
            df['soup'] = df.apply(create_soup, axis=1)
            tfidf_matrix = tfidf.fit_transform(df['soup'])
            indices = pd.Series(df.index, index=df['url']).drop_duplicates()
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
            index = indices[post['url']]
            sim_scores = list(enumerate(cosine_sim[index]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:11]
            movie_indices = [i[0] for i in sim_scores]
            return df['url'].iloc[movie_indices].values.tolist()

    def get_id(self, url):
        new = re.sub('/in/.*', '', url)
        items = new.split('/')
        return items[-1]

    def remove_query(self, string):
        new = re.sub('/\?tagged=.*$', '', string)
        return new


def get_comments(x):
    comments = list()
    for i in x:
        comments.append(MongoConnector.clean_string(i['comment']))
    return comments


def create_soup(x):
    soup = x['title'] + ' ' + x['description'] + ' ' + ' '.join(x['hashtags']) + ' ' +\
        ' '.join(x['comments_hashtags'])
    return soup


def remove_from_all(x):
    result = list()
    for i in x:
        new = remove_other_languages(i)
        result.append(new)
    return result


def remove_other_languages(x):
    if x:
        split = nltk.wordpunct_tokenize(x.encode('ascii', 'ignore').decode())
        for w in split:
            if w:
                if not w.lower() in words:
                    split.remove(w)
        return ' '.join(split)
    return ''


if __name__ == '__main__':
    recommender = Recommender()
    recommendation = recommender.get_recommendations('https://www.instagram.com/p/BoJzU6fDwHR/?tagged=tennis')
    recommendation_2 = recommender.get_recommendations('https://www.instagram.com/p/BoJ4PXgDElX/?tagged=food')
    print('%s' % recommendation)
    print('%s' % recommendation_2)
