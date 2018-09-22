import sys, argparse, os
from instagramscraper import InstagramScraper


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
    parser.add_argument('-u', '--username', type=str,
                        help='The username of the profile to be scraped, can be also a list or a txt file',
                        required=False, dest='u')

    args = parser.parse_args()
    if args.f == "scraper":
        if not (args.t or args.u):
            print("At least an hashtag or a user must be defined")
            sys.exit(1)
        scraper = InstagramScraper()
        driver = scraper.establish_connection()
        if args.t:
            inp = check_input(args.t)
            if inp == 0:
                with open(args.t) as tag_file:
                    for line in tag_file:
                        scraper.scrape_hashtag(driver, line)
            elif inp == 1:
                for tag in args.t:
                    scraper.scrape_hashtag(driver, tag)
            elif inp == 2:
                scraper.scrape_hashtag(driver, args.t)
        if args.u:
            inp = check_input(args.u)
            if inp == 0:
                with open(args.u) as user_file:
                    for line in user_file:
                        scraper.scrape_user(driver, line)
            elif inp == 1:
                for user in args.u:
                    scraper.scrape_user(driver, user)
            elif inp == 2:
                scraper.scrape_user(driver, args.u)
        scraper.end_connection(driver)
    else:
        print("Invalid function, type -h for more info")
        sys.exit(1)


if __name__ == '__main__':
    main()
