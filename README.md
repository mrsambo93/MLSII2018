# MLSII2018
Per far funzionare lo scraper:
  1) scaricare il webdriver di Chrome per il sistema operativo corrente da http://chromedriver.chromium.org/downloads 
  2) estrarre il driver nella cartella chromedriver
  3) in scraper.py trovare la linea 
      ```
      driver = webdriver.Chrome('./chromedriver/chromedriver', chrome_options=opts)
      ```
     e sostituire il path con quello corretto
  4) nella cartella del progetto creare un file credentials.json con le credenziali di accesso ad instagram nella forma:
      ```
      {
        "user" : "xxx",
        "password" : "xxx"
      }
      ```
