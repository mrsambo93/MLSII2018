import sys, argparse, os
from instagramscraper import InstagramScraper
from flickrscraper import FlickrScraper
from recommender import Recommender
from mongoconnector import MongoConnector


def check_input(inp):
    if '.txt' in inp and os.path.exists(inp):
        return 0
    elif isinstance(inp, (list,)):
        return 1
    return 2


def main():
    parser = argparse.ArgumentParser(description='Project argument parser')
    parser.add_argument('-f', '--function', type=str, help='The function, can be either scraper or recommender',
                        required=True, dest='f')
    parser.add_argument('-t', '--tag', type=str,
                        help='The hashtag to be scraped, can be also a list or a txt file',
                        required=False, dest='t')
    parser.add_argument('-u', '--url', type=str,
                        help='The url of the post which you want to find similar',
                        required=False, dest='u')

    args = parser.parse_args()
    if args.f == "scraper":
        if not args.t:
            print("At least an hashtag must be defined")
            sys.exit(1)
        instagram_scraper = InstagramScraper()
        flickr_scraper = FlickrScraper()
        driver = instagram_scraper.establish_connection()
        flickrapi = flickr_scraper.establish_connection()
        if args.t:
            inp = check_input(args.t)
            if inp == 0:
                with open(args.t) as tag_file:
                    for line in tag_file:
                        instagram_scraper.scrape_hashtag(driver, line)
                        flickr_scraper.scrape_hashtag(flickrapi, line)
            elif inp == 1:
                for tag in args.t:
                    instagram_scraper.scrape_hashtag(driver, tag)
                    flickr_scraper.scrape_hashtag(flickrapi, tag)
            elif inp == 2:
                instagram_scraper.scrape_hashtag(driver, args.t)
                flickr_scraper.scrape_hashtag(flickrapi, args.t)
        instagram_scraper.end_connection(driver)
        # MongoConnector.translate_to_english('sport')
        # MongoConnector.translate_to_english('food')
    elif args.f == 'recommender':
        if args.u:
            recommender = Recommender()
            recommendation = recommender.get_recommendations(args.u)
            print('The best matches are: %s' % recommendation)
        else:
            print('Invalid argument, should be -u or --url')
            sys.exit(1)
    else:
        print("Invalid function, type -h for more info")
        sys.exit(1)


if __name__ == '__main__':
    main()
