#Libraries for Web Scraping process
import requests
from bs4 import BeautifulSoup
from  IPython.core.display import clear_output

#Libraries for Data Wrangling and Data Cleaning
import numpy as np
import re
from itertools import groupby
import pandas as pd


def webscraping_jobs(search,pages):
    """ START OF  WEB SCRAPING CODE"""

    #Create new lists to store information 

    titles = []
    regions = []
    features = []
    glosas = []
    profiles = []
    target_urls = []

    #create the target url of the main webpage based on the search parameter (This is different for each webpage) 
    front_url = "trabajo-de-"+search.replace(" ","-")
    back_url = search.replace(" ", "%20")
    main_url = 'https://www.computrabajo.cl/'

    
    print("Running Web Scraping...")

    #Iterate over the  number of  pages to extract the information on the  job offers containers.
    for page in range(1,pages+1):

        url = main_url + front_url + "?q=" + back_url +'&p=' + str(page)
        main_response = requests.get(url)
        main_soup = BeautifulSoup(main_response.text,'html.parser')
        soup_urls = main_soup.find_all('a',class_='js-o-link')
        
        # Iterate over each of the job offers containers to obtain the url for each job offer and append the results into the list target_urls 
        for uri in soup_urls:
            target_urls.append(main_url+uri['href'])


    #Iterate for each of the urls on target_urls list to extract the  target information of each job offer.
    for target in target_urls:  


        response = requests.get(target)
        soup = BeautifulSoup(response.text,'html.parser')

        #Separate the HTML code  of each job offer page in 2 main distributions (description and table)
        #(this is different for each webpage)

        #Obtain the frame of description 
        try:
            description_frame = soup.find_all('ul',class_='p0 m0')[0]
            table_frame = soup.find_all('ul',class_='p0 m0')[1]
        except (AttributeError,IndexError):
            pass


        #extract the main features of frame table and store them in the lists created above
        try: 
            temp_title = table_frame.find_all('p')[0]
            titles.append(temp_title.text)
        except (AttributeError,IndexError):
            titles.append("nan")
        try:
            temp_region = table_frame.find_all('p')[1]
            regions.append(temp_region.text)
        except (AttributeError,IndexError):
            regions.append("nan")

        try:
            feature = table_frame.find_all('p',class_='fw_b fs15 mt10')
            temp_feature = []
            for ix in range(0,len(feature)):
                temp_feature.append(feature[ix].find_next_sibling().text.strip())
            
            features.append(temp_feature)
        
        except (AttributeError,IndexError):
            features.append("nan")

        #extract the main features of frame description and store them in the lists created above
        try:
            temp_glosa = description_frame.find_all('li')[1]
            glosas.append(temp_glosa.text)
        except (AttributeError,IndexError):
            glosas.append("nan")
        try:
            temp_profile = description_frame.find_all('li')[3:]
            profiles.append(temp_profile)
        except (AttributeError,IndexError):
            profiles.append("nan")
        
        print(f"Extracting Job Offers for {search}: {len(titles)}")
        clear_output(wait=True)

    print("Web Scraping Finished!")
    print(f"Total Job Offers Extracted: {len(titles)}")

    """ END  OF WEB SCRAPING CODE"""


    """ START OF DATA WRANGLING AND DATA CLEANING CODE"""

    #Create new lists to store final features

    companies = []
    contracts = []
    journeys = []
    salaries = []
    travels = []
    residence = []
    experience = []
    regs = []

    #extract the target values of each feature from  the lists created using the web scraping
    for feature in features:
        if len(feature)==2:
            contracts.append(feature[0])
            journeys.append(feature[1])
            companies.append("nan")
            salaries.append("nan")
        if len(feature)==4:
            companies.append(feature[0])
            contracts.append(feature[1])
            journeys.append(feature[2])
            salaries.append(feature[3])

        if len(feature)==3 and "$" in feature[2]:
            contracts.append(feature[0])
            journeys.append(feature[1])
            salaries.append(feature[2])
            companies.append("nan")

        if len(feature)==3 and not "$" in feature[2]:
            companies.append(feature[0])
            contracts.append(feature[1])
            journeys.append(feature[2])
            salaries.append("nan")

    #clean  text values of travels, residence and experience using regex 
    for profile in profiles:
        for prop in profile:
            reg_travel = re.findall(r"viajar:\s\w*",str(prop))
            reg_resid = re.findall(r"residencia:\s\w*",str(prop))
            reg_exp = re.findall(r"experiencia: \d*",str(prop))

            if reg_travel:
                travels.append(str(reg_travel)) 
            if reg_resid:
                residence.append(str(reg_resid))
            if reg_exp:
                experience.append(str(reg_exp))
        
        if not reg_exp in profile:
            experience.append("nan")
        
    #Extract the information of education 
    education =  [str(t[0]) for t in profiles]

    #Clean lists of features travels, residence, experience and title
    experience = [x for y in (list(amount) if value != "nan" else ["nan"] * (len(list(amount))-1)
                    for value, amount in groupby(experience)) for x in y if x]
    experience = [s.replace("['experiencia: ","").replace("']","") for s in experience]
    if len(experience) != len(titles):
        experience.append("nan")

    travels = [s.replace("['viajar: ","").replace("']","") for s in travels ]
    residence = [s.replace("['residencia: ","").replace("']","") for s in travels ]

    titles = [s.replace("\r\n","").strip() for s in titles]
    regions = [s.replace("\r\n","").strip() for s in regions]
    glosas = [s.replace("•","").replace("\t","").strip() for s in glosas]
    salaries = [s.replace("(Neto mensual)","").replace("$","").replace(".","").replace(",",".") for s in salaries]
    
    

    #Filter by region and clean values
    regions2 = [s.split("-") for s in regions]
    for region in regions2:
        if len(region)==1:
            regs.append(region[0])
        if len(region)==2:
            regs.append(region[1])

    #mantain the same length of  experience and titles features (to avoid length conflicts)
    if len(experience) != len(titles):
        experience.append("nan")

    #Store the final features on Data Frame
    df = pd.DataFrame({'oferta':titles,'region':regs,'empresa':companies,'salario':salaries,'experiencia':experience,'viajes':travels,
                      'residencia':residence,'jornada':journeys,'contrato':contracts,'educacion':education,'glosa':glosas,'url':target_urls})

    return df

    