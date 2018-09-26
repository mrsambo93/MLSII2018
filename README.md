# MLSII2018
Per far funzionare lo scraper:
  1) scaricare il webdriver di Chrome per il sistema operativo corrente da http://chromedriver.chromium.org/downloads 
  2) estrarre il driver nella cartella chromedriver
  3) in scraper.py trovare la linea 
      ```
      driver = webdriver.Chrome('./chromedriver/chromedriver', chrome_options=opts)
      ```
     e sostituire il path con quello corretto
  4) nella cartella del progetto creare un file credentials.json con le credenziali di accesso ad instagram e le key e secret       per le api di flickr:
      ```
      {
        "user" : "xxx",
        "password" : "xxx",
        "flickr_key": "43913328ddd9b2625e23bc41f8ebe526",
        "flickr_secret": "9777059efea7172c""
      }
      ```
  5) lanciare un'istanza di mongodb sulla porta di default:
      ```
      $ mongod
      ```
  6) eseguire l'installazione di setup.py
      ```
      $ python setup.py install
      ```
  7) per lanciare lo scraping di un hashtag (e.g. "#sport"):
      ```
      $ python main.py -f "scraper" -t "#sport"
      ```
Per le raccomandazioni a partire da un url:
    ```
    $python main.py -f "recommender" -u "<instagram-or-flickr-post-url>"
    ```
