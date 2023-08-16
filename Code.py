from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
from distutils.log import debug
from fileinput import filename
from flask import *
import os
from werkzeug.utils import secure_filename
df = []
UPLOAD_FOLDER = os.path.join('staticFiles', 'uploads')
 
ALLOWED_EXTENSIONS = {'csv'}
 
app = Flask(__name__)
 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
 
app.secret_key = 'This is your secret key to utilize session in Flask'  

@app.route('/extract')
def extract_data(searchKey="Laptop"):
    
   driver = webdriver.Chrome()
   driver.get("https://www.amazon.in")

   
   search = driver.find_element(By.ID, "twotabsearchtextbox")
   submit = driver.find_element(By.ID, "nav-search-submit-button")
   search.send_keys(searchKey)
   search.send_keys(Keys.RETURN)
   
   driver.implicitly_wait(5)

   product_name = []
   product_asin = []
   product_price = []
   product_link = []
   products={}
 

   def data_extraction():
      try:
         items = WebDriverWait(driver,100).until(EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "s-result-item s-asin")]')))

         for item in items:
           
            try:
               name = item.find_element(By.XPATH, './/span[@class="a-size-medium a-color-base a-text-normal"]')
               product_name.append(name.text)
             

               data_asin = item.get_attribute("data-asin")
               product_asin.append(data_asin)
         
               price = item.find_element(By.XPATH, './/span[@class="a-price-whole"]')
               product_price.append(price.text)
         
               link = item.find_element(By.XPATH, './/*[@class="a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"]').get_attribute("href")
               product_link.append(link)
               products[name.text]={"price":price.text,"link":link}
            except :
               pass
            
      except :
         print("Not Possible")
         
   print("here2")
   total_pages = 2
   for _ in range(1, total_pages+1):
      data_extraction()
      driver.implicitly_wait(2)
      try:
         next = WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.LINK_TEXT, "Next")))
         next.click()
      except NoSuchElementException:
         print("Not Possible")
         break
      time.sleep(2)

   product_csv={"Name":product_name,"price":product_price,"link":product_link}
   driver.implicitly_wait(2)
   driver.quit()
   df = pd.DataFrame(product_csv)
   df.to_csv('Product_list.csv')
   session['df'] = 'Product_list.csv' 
   
   #driver.quit()
   return redirect("/")

@app.route('/', methods=['GET'])
def showData():
   
   # chrome_options = Options()  
   # chrome_options.add_argument("--headless") 
   # chrome_options.add_argument("--window-size=1200,600")
   # chrome_options.add_argument('--start-maximized')
   # chrome_options.add_argument('--disable-gpu')
   # chrome_options.add_argument('--no-sandbox')
   # chrome_options.add_argument("--disable-extensions")
   # chrome_options.add_argument('disable-infobars')
   
   df_path= session.get('df', None)
   if not df_path:
      extract_data("Laptop")
   df = pd.read_csv(session.get('df', None))
   uploaded_df_html = df.to_html()
   return render_template('page.html', data_var=uploaded_df_html)

@app.route('/', methods=['POST'])
def read_Data():
   data = request.form  
   searchkey = data['searchkey']
   df_path= session.get('df', None)
   if not df_path:
      extract_data(searchkey)
   else:
      df = pd.read_csv(session.get('df', None))
      #print(df.head())
      df["Indexes"] = df["Name"].str.find(searchkey)
      df = df.where(df["Indexes"] != -1)
      df.dropna(axis='index',inplace=True)
      df.drop(["Indexes"], axis=1,inplace=True)
      if df.empty:
         extract_data(searchkey)
         df = pd.read_csv(session.get('df', None))
   uploaded_df_html = df.to_html()
   return render_template('page.html', data_var=uploaded_df_html)

if __name__ == '__main__':
    app.run(debug=True)



