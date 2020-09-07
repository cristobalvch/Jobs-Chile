import requests
from bs4 import BeautifulSoup
from  IPython.core.display import clear_output
import numpy as np
import re

from itertools import groupby
import pandas as pd


def webscraping_jobs(search,pages):

    #Listas donde se guardará la información 

    titles = []
    regions = []
    features = []
    glosas = []
    profiles = []
    target_urls = []


    front_url = "trabajo-de-"+search.replace(" ","-")
    back_url = search.replace(" ", "%20")
    main_url = 'https://www.computrabajo.cl/'

    #Obtener lista con urls de ofertas de trabajo por cada pagina principal de busqueda
    print("Iniciando Web Scraping...")
    
    for page in range(1,pages+1):

        url = main_url + front_url + "?q=" + back_url +'&p=' + str(page)
        main_response = requests.get(url)
        main_soup = BeautifulSoup(main_response.text,'html.parser')
        soup_urls = main_soup.find_all('a',class_='js-o-link')

        for uri in soup_urls:
            target_urls.append(main_url+uri['href'])

    #Iterar por cada una de las ofertas de trabajo para obtener informacion 

    for target in target_urls:  


        response = requests.get(target)
        soup = BeautifulSoup(response.text,'html.parser')

        #Separar el codigo html de la url en los dos frames principales
        try:
            description_frame = soup.find_all('ul',class_='p0 m0')[0]
            table_frame = soup.find_all('ul',class_='p0 m0')[1]
        except (AttributeError,IndexError):
            pass


        #Informacion del frame de tabla
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

        #Informacion del frame de descripsion
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
        
        print(f"Extrayendo Ofertas Laborales para {search}: {len(titles)}")
        clear_output(wait=True)

    print("Web Scraping Finalizado!")
    print(f"Total de Ofertas laborales extraidas: {len(titles)}")

    #creacion de listas donde se guardaran datos finales

    companies = []
    contracts = []
    journeys = []
    salaries = []
    travels = []
    residence = []
    experience = []
    regs = []

    #extraccion de valores objetivo de lista general feature
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

    #extraer informacion  de criterio viajes,residencia y experiencia  con regex
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

    education =  [str(t[0]) for t in profiles]
    
    #limpiar listas de criterios viajes, residencias, experiencias, titulo
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
    
    

    #Filtrar y limpiar regiones
    regions2 = [s.split("-") for s in regions]
    for region in regions2:
        if len(region)==1:
            regs.append(region[0])
        if len(region)==2:
            regs.append(region[1])

    if len(experience) != len(titles):
        experience.append("nan")

    
    df = pd.DataFrame({'oferta':titles,'region':regs,'empresa':companies,'salario':salaries,'experiencia':experience,'viajes':travels,
                      'residencia':residence,'jornada':journeys,'contrato':contracts,'educacion':education,'glosa':glosas,'url':target_urls})

    return df

    