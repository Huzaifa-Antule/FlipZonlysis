""" Amazon_Flipkart_Analysis for a Product  Analysis.
    
    Original file is located at
        https://colab.research.google.com/drive/1NpeglCLXMbg3yPkqvt8aJECUwO88-LRX
"""

# Importing Libraries/Packages.

import requests
from bs4 import BeautifulSoup
import pandas as pd
from fake_useragent import UserAgent
import time
from urllib.parse import quote
import pandas as pd
import matplotlib.pyplot as plt
from fuzzywuzzy import process, fuzz

# Search Section
def Search_Product(Product_name:str):
  """
      returns links for both Flipkart & Amazon.
  """
  Amazon_Url = f"https://www.amazon.in/s?k={Product_name.replace(' ','+')}"
  Flipkart_Url = f"https://www.flipkart.com/search?q={quote(Product_name)}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off"
  print(f"Checkout Amazon Here: {Amazon_Url}")
  print(f"Checkout Flipkart Here: {Flipkart_Url}")
  
  return Amazon_Url,Flipkart_Url

# Auto-Response Section
def Get_Response(url:str,product_name:str= None,platform:str=None):
  """
    Returns Response if Status Code is 200.

    Args:
      url - String: Url of the products to be scraped.

    Returns:
      Page - HTML Response.
      or
      Warning Message.
  """
  start_time = time.time()
  while time.time() - start_time < 30:
    headers = {
      "User-Agent": UserAgent().chrome,
      "Accept-Language": "en-US,en;q=0.5"
    }
    Page = requests.get(url,headers=headers)
    if Page.status_code == 200:
      print(f"Successfull Response from {platform if platform  else 'Url'} for { product_name if product_name else 'Product'} with {Page.status_code} Code.")
      return Page
    else:
      time.sleep(2)
      continue
  else:
    print("Loop finished after 30 seconds without a successful response.")

# Amazon Scraping Section
def Amazon_Scraping(Amazon_Url:str,Product_name:str=None):
  """
    Scrapes Amazon Page for Product Name.
    
    Args:
      Amazon_Url - String: Url of the products to be scraped.
      Product_Name - String: Product Name.
    
    Returns:
      Pandas DataFrame of Scraped Products with the following fields:
        - Product Name
        - Product Price
        - Product Link
        - Previous Boughts
  """
  try:
    Amazon_Response = Get_Response(Amazon_Url,Product_name,"Amazon.in")
    Amazon_Soup = BeautifulSoup(Amazon_Response.content,"html.parser")
    Amazon_divs = Amazon_Soup.find_all("div", class_="puisg-col-inner")
    Amazon_Products = {"Product Name": [], "Product Link": [], "Product Boughts": [], "Product Price": []}
    for i in Amazon_divs:
        Price = i.find('span', attrs={'class': 'a-price-whole'})

        # Check for "Sponsored" before processing the product
        sponsored_element = i.find('span', attrs={'class': 'a-size-mini a-color-secondary'})
        if sponsored_element and sponsored_element.text == "Sponsored":
            continue  # Skip this product if it's sponsored

        if Price is not None:
            try:
                Product_Description = i.find('h2').text
                Product_Link = "https://www.amazon.in" + i.find('a').get('href')
                Product_Price = int(Price.text.strip().replace(',',''))
                Product_Boughts = sponsored_element.text if sponsored_element else "N/A"  # Use "N/a" if sponsored_element is None

                Amazon_Products['Product Name'].append(Product_Description)
                Amazon_Products['Product Link'].append(Product_Link)
                Amazon_Products['Product Boughts'].append(Product_Boughts)
                Amazon_Products['Product Price'].append(Product_Price)
            except Exception as e:
                print(e)
    return pd.DataFrame(Amazon_Products)

  except Exception as e:
    print(e)

# Flipkart Scraping Section
def Flipkart_Scraping(Flipkart_Url:str,Product_name:str=None):
  """
    Scrapes Flipkart Page for Product Name.
    
    Args:
      Flipkart_Url - String: Url of the products to be scraped.
      Product_name - String: Product name.
    
    Returns:
      Pandas DataFrame of Scraped Products with the following fields:
        - Product Name
        - Product Price
        - Product Link
        - Product Details
  """
  try:
    Flipkart_Response = Get_Response(Flipkart_Url,Product_name,"Flipkart.com")
    Flipkart_Soup = BeautifulSoup(Flipkart_Response.text,"html.parser")
    Flipkart_Products = {'Product Name':[],'Product Link':[],'Product Price':[],'Product Details':[]}
    while True:
      Divs = Flipkart_Soup.find_all('div', class_='tUxRFH')
      if Divs:
        break
      else:
          Flipkart_Response = Get_Response(Flipkart_Url,Product_name,"Flipkart.com")
          Flipkart_Soup = BeautifulSoup(Flipkart_Response.text,"html.parser")   
          continue         
    for div in Divs:
      Flipkart_Products['Product Name'].append(div.find('div',class_='KzDlHZ').text)
      Flipkart_Products['Product Price'].append(int(div.find('div',class_='_4b5DiR').text[1:].replace(',', '')))
      Flipkart_Products['Product Link'].append("https://www.flipkart.com"+div.find('a',class_='CGtC98').get('href'))
      Flipkart_Products['Product Details'].append('\n'.join(str(item) for item in [i.text for i in div.find_all('li', class_='J+igdf')]))
    
    return pd.DataFrame(Flipkart_Products)
  except Exception as e:
    print(e)

# Raw Dataframes Processing
def Cleaned_Data_Frames(Amazon_Dataframe,Flipkart_Dataframe):
  """
    Takes Two Data Frames i.e Amazon,Flipkart as input and returns cleaned data frames.
  """
  df1 = Amazon_Dataframe.drop('Product Boughts', axis=1)
  df2 = Flipkart_Dataframe.drop('Product Details', axis=1)
  
  return df1,df2

# Flipkart v/s Amazon Data Analysis
class Flipkart_Amazon_Analysis:
    """
      Performs Analysis based on Amazon and Flipkart Dataframes.
      Includes:
        - Compare Prices.
        - Show Prices Statistics.
        - Show Price Comparison in Chart.
      
      Args:
        - Amazon Data Frame: DataFrame - Amazon Products DataFrame.
        - Flipkart Data Frame: DataFrame - Flipkart Products DataFrame.
    """
    def __init__(self, amazon_df, flipkart_df):
        self.amazon_df = amazon_df
        self.flipkart_df = flipkart_df
        self.price_comparison = None
        self.amazon_price_stats = None
        self.flipkart_price_stats = None

    def match_product(self, flipkart_product):
            """Matches a product name from Flipkart to the most relevant product in Amazon."""
            # Check for exact matches first
            exact_matches = self.amazon_df[self.amazon_df['Product Name'] == flipkart_product]
            if not exact_matches.empty:
                return exact_matches.iloc[0]['Product Name']  # Return the exact match product name

            # If no exact match, fall back to fuzzy matching
            fuzzy_match = process.extractOne(
                flipkart_product, 
                self.amazon_df['Product Name'].tolist(), 
                scorer=fuzz.token_sort_ratio
            )
            return fuzzy_match[0] if fuzzy_match else None

    def compare_price(self):
          """Compares prices of products from Flipkart and Amazon."""
          # Add a new column for matched Amazon product names
          self.flipkart_df['Matched Amazon Product Name'] = self.flipkart_df['Product Name'].apply(
              lambda x: self.match_product(x) if pd.notnull(x) else None
          )

          # Merge Flipkart and Amazon data based on matched product names
          self.price_comparison = pd.merge(
              self.flipkart_df,
              self.amazon_df,
              left_on='Matched Amazon Product Name',
              right_on='Product Name',
              how='inner',
              suffixes=('_Flipkart', '_Amazon')
          )

          # Handle cases where multiple products have the same name
          self.price_comparison = self.price_comparison.groupby(
              ['Product Name_Flipkart', 'Product Name_Amazon']
          ).agg({
              'Product Link_Flipkart': 'first',
              'Product Link_Amazon': 'first',
              'Product Price_Flipkart': 'mean',
              'Product Price_Amazon': 'mean'
          }).reset_index()

          # Calculate price difference
          self.price_comparison['Price Difference'] = (
              self.price_comparison['Product Price_Flipkart'] - self.price_comparison['Product Price_Amazon']
          )

          return self.price_comparison

    def show_price_stats(self):
        """Calculates and displays statistics for product prices on Amazon and Flipkart."""

        self.amazon_price_stats = f"Amzon Price Stats:\n{self.amazon_df['Product Price'].describe()}"
        self.flipkart_price_stats = f"Flipkart Price Stats:\n{self.flipkart_df['Product Price'].describe()}"

        return self.amazon_price_stats, self.flipkart_price_stats

    def show_price_comparison(self):
        """Returns price comparison between Amazon and Flipkart for each product as a chart."""

        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure

        # Price Distribution
        fig = Figure(figsize=(10, 6))
        ax = fig.add_subplot(1, 1, 1)
        ax.hist(self.amazon_df['Product Price'], bins=20, alpha=0.5, label='Amazon')
        ax.hist(self.flipkart_df['Product Price'], bins=20, alpha=0.5, label='Flipkart')
        ax.set_xlabel('Price')
        ax.set_ylabel('Product Count')
        ax.set_title('Price Distribution')
        ax.legend()

        return fig

      
if __name__=="__main__":
  Product_name = input("Enter the product name: ")
  Amazon_Url,Flipkart_Url = Search_Product(Product_name)
  
  Amazon_Data = Amazon_Scraping(Amazon_Url=Amazon_Url)
  Flipkart_Data = Flipkart_Scraping(Flipkart_Url=Flipkart_Url)
  
  # Cleaning
  Amazon_Data_Cleaned,Flipkart_Data_Cleaned = Cleaned_Data_Frames(Amazon_Data,Flipkart_Data)
  
  # Analysis
  Analysis = Flipkart_Amazon_Analysis(Amazon_Data_Cleaned,Flipkart_Data_Cleaned)
  
  Analysis.compare_price().to_csv(f"{Product_name}_Price_Anlysis.csv",index=False)
  
  Amazon_Stats,Flipkart_Stats = Analysis.show_price_stats()
  print(Amazon_Stats)
  print(Flipkart_Stats)
  
  Analysis.show_price_comparison()
