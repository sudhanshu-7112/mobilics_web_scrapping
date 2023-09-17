import pymongo
from django.http import JsonResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time


######################## THESE ARE THE URLS OF DIFFERENT CITIES WE NEED TO SCRAP DATA ######################################################

URL = ["https://99acres.com/search/property/buy/hyderabad-all?city=38&preference=S&area_unit=1&res_com=R "
       "https://www.99acres.com/search/property/buy/lucknow?city=205&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/pune?city=19&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/delhi?city=1075722&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/mumbai-all?city=12&preference=S&area_unit=1&res_com=R&",
       "https://www.99acres.com/search/property/buy/agra?city=197&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/ahmedabad-all?city=45&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/kolkata-all?city=25&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/jaipur?city=177&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/chennai-all?city=32&preference=S&area_unit=1&res_com=R",
       "https://www.99acres.com/search/property/buy/bangalore-all?city=20&preference=S&area_unit=1&res_com=R"]

######## THIS IS THE FUNCTION TO CONNECT WITH MONGODB ###################################
def connect_to_db():
    connect_string = 'mongodb://localhost:27017' 
    my_client = pymongo.MongoClient(connect_string)
    return my_client


################################################# THE MAIN FUNCTION TO SCRAP THE DATA ###########################################

def scrap_data():

    # connect_to_db() function is called to make connection with db
    my_client = connect_to_db()

    # settings applied to run headless browser in incongnito mode using selenium
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--incognito")
    driver = webdriver.Chrome(options=options)


    l = []
    # looping through each CITY
    for url in URL:
        # it fetches the url of the city
        driver.get(url)

        # index variable is used to know the no of pages we visit for the particular city
        index = 1

        # we don't know the no of page for a particular city so we will go to next page until we met with error
        while(True):

            # 2 sec sleep is necessary as 99acres.com will block our request as we sends too many requests
            time.sleep(2)

            # fetch the html section of the page using selenium

            value = driver.find_element(By.CLASS_NAME,"r_srp__rightSection")
            x = value.get_attribute("innerHTML")

            soup = BeautifulSoup(x, 'html.parser')


            # loop to all the apartments, land, etc on the page using BeautifulSoup
            for i in soup.find_all('div',{'class':'projectTuple__tupleDetails projectTuple__premiumWrapper projectTuple__fsl'}):
                # fetch property name
                property_name = i.find('a',{'class':'projectTuple__projectName projectTuple__pdWrap20 ellipsis'}).text
                # fetch html of property details like property type, property area, property cost
                property_details = i.find_all('div',{'class':'configurationCards__cardContainer configurationCards__srpCardStyle'})
                # fetch locality details like property locality and city
                locality_details = i.find('h2',{'class':'projectTuple__subHeadingWrap body_med ellipsis'}).text.split('in')[1].split(',')
                property_locality = locality_details[0]

                # this if statement condition was made because error in 99acres.com site html was incomplete
                if len(locality_details)>1:
                    property_city = locality_details[1]
                else:
                    property_city = '---'
                
                # looping through property details
                for j in property_details:
                    # property_type1 fetches whether the no of bhk like 2 BHK, 3 BHK or Land
                    property_type1 = j.find('span',{'class':'list_header_semiBold configurationCards__configBandLabel'}).text
                    # property_type2 fetches the type of property like apartmnet, villa, etc
                    property_type2 = j.find('span',{'class':'caption_subdued_medium configurationCards__configBandHeading'}).text

                    if property_type2 == None:
                        property_type2 = ''
                    
                    property_type = property_type1+' '+property_type2

                    # we fetch property cost and area if error comes we move to next
                    try:
                        property_cost = j.find('span',{'class':'list_header_semiBold configurationCards__cardPriceHeading'}).text
                        property_area = j.find('span',{'class':'caption_subdued_medium configurationCards__cardAreaSubHeadingOne'}).text
                    except:
                        continue
                    
                    # we append the data to the list
                    l.append({'property_name':property_name.strip(),'property_type':property_type.strip(),'property_cost':property_cost.strip(),'property_area':property_area.strip(),'property_locality':property_locality.strip(),'property_city':property_city.strip()})
            
            # we try to move next page if error comes we move to next city
            try:
                element = driver.find_elements(By.CLASS_NAME, "list_header_bold")
                driver.execute_script("arguments[0].click()",element[-1])
            except:
                break

            index+=1
    
    # we quit the driver
    driver.quit()
    
    #we coonect to db
    db = my_client['mobilics']

    # we make a collection name scrapping
    collection = db['scrapping']
    # if previous scrapping exist we delete it
    collection.drop()

    # we insert data in the collection scrapping
    collection = db['scrapping']
    collection.insert_many(l)

    return JsonResponse({'msg':'Success'})


############################ AN API TO SCRAP DATA USING HTTP REQUEST #################################################
def scrapping(request):
    return scrap_data()