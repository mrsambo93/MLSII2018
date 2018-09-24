import pymongo, json
from tqdm import tqdm


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
            self.mongo_client = pymongo.MongoClient("mongodb+srv://mrsambo93:" +
                                                    credentials["mongodb_password"] +
                                                    "@mlsii2018-vh1jw.mongodb.net/MLSII2018?retryWrites=true")
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
        connector.db.posts.create_index([('url', pymongo.ASCENDING)], unique=True)
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
