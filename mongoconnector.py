import pymongo, json
from tqdm import tqdm
from googletrans import Translator
import unicodedata


class MongoConnector:
    __instance = None
    mongo_client = None
    db = None

    def __init__(self):
        if MongoConnector.__instance:
            raise Exception("Singleton!")
        else:
            MongoConnector.__instance = self
            with open("credentials.json", "r") as json_file:
                credentials = json.load(json_file)
            try:
                if credentials['mongodb_password']:
                    self.mongo_client = pymongo.MongoClient("mongodb+srv://mrsambo93:" +
                                                        credentials["mongodb_password"] +
                                                        "@mlsii2018-vh1jw.mongodb.net/MLSII2018?retryWrites=true")
                else:
                    self.mongo_client = pymongo.MongoClient('localhost', 27017)
            except KeyError:
                self.mongo_client = pymongo.MongoClient('localhost', 27017)
            self.db = self.mongo_client.MLSII2018

    @staticmethod
    def get_instance():
        if not MongoConnector.__instance:
            MongoConnector()
        return MongoConnector.__instance

    @staticmethod
    def save_to_db(posts, tag):
        print('\nSaving on db')
        connector = MongoConnector.get_instance()
        connector.db[tag].create_index([('url', pymongo.ASCENDING)], unique=True)
        pos = connector.db[tag]
        for post in tqdm(posts):
            res = pos.replace_one({'url': post["url"]}, post)
            if res.modified_count == 0:
                pos.insert_one(post)

    @staticmethod
    def clean_db():
        connector = MongoConnector.get_instance()
        collection_names = connector.db.list_collection_names()
        for collection in collection_names:
            connector.db[collection].remove({})

    @staticmethod
    def get_posts_by_tag(tag):
        connector = MongoConnector.get_instance()
        return list(connector.db[tag].find({}))

    @staticmethod
    def get_all_posts():
        connector = MongoConnector.get_instance()
        res = list()
        for coll in connector.db.list_collection_names():
            res.extend(connector.db[coll].find())
        return res

    @staticmethod
    def find_post(query):
        connector = MongoConnector.get_instance()
        result = None
        for coll in connector.db.list_collection_names():
            result = connector.db[coll].find_one(query)
        return result

    @staticmethod
    def remove_by_source(source):
        connector = MongoConnector.get_instance()
        for coll in connector.db.list_collection_names():
            connector.db[coll].delete_many({'source': source})

    @staticmethod
    def update_db(posts, tag):
        print('\nUpdating')
        connector = MongoConnector.get_instance()
        pos = connector.db[tag]
        for post in tqdm(posts):
            pos.replace_one({'_id': post['_id']}, post)

    @staticmethod
    def translate_to_english(tag):
        posts = MongoConnector.get_posts_by_tag(tag)
        print('\nTranslating posts to english')
        new_posts = list()
        for post in tqdm(posts):
            new_post = dict(post)
            translator = Translator()
            try:
                title = MongoConnector.clean_string(post['title'])
                new_post['title'] = translator.translate(title).text
            except KeyError:
                new_post['title'] = ''
            description = MongoConnector.clean_string(post['description'])
            print(description)
            translator = Translator()
            new_post['description'] = translator.translate(description).text
            comments = post['comments']
            new_comments = list()
            for comment in comments:
                translator = Translator()
                new_comment = dict()
                new_comment['commenter'] = comment['commenter']
                c = MongoConnector.clean_string(comment['comment'])
                new_comment['comment'] = translator.translate(c).text
                new_comments.append(new_comment)
            new_post['comments'] = new_comments
            new_posts.append(new_post)
        MongoConnector.update_db(new_posts, tag)

    @staticmethod
    def clean_string(string):
        new_text = []
        for c in unicodedata.normalize('NFC', string.replace('\n', ' ')):
            if ord(c) < 128:
                # this is optional, it add ascii character as they are
                # possibly you want to tokenize (see later, how we replace punctuation)
                new_text.append(c)
                continue
            cat = unicodedata.category(c)
            if cat in {'Lu', 'Ll', 'Lt', 'Lm', 'Lo', 'Nd'}:
                new_text.append(c)
            elif cat in {'Mc', 'Pc', 'Pd', 'Ps', 'Pe', 'Pi', 'Of', 'Po', 'Zs', 'Zl', 'Zp'}:
                # this tokenize
                new_text.append(' ')
        result = ''.join(new_text)
        result = [tag for tag in result.split() if not (tag.startswith('#') or tag.startswith('@'))]
        return ' '.join(result).lower()
