# -*- coding: utf-8 -*-
"""
Created on Sat Feb 13 21:57:27 2021

@author: Ray
"""


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time
import json
from datetime import datetime
import random
import os
import urllib.request
now = datetime.now()
current_time = now.strftime("%Y_%m_%d_%H_%M_%S")


def connect_to_nord():
    current_path = os.path.dirname(os.path.realpath(__file__))
    current_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
    us_city_server_groups = ['Atlanta', 'Chicago', 'Denver', 'Manassas',\
                             'Miami', 'Phoenix', 'San Jose', 'Salt Lake City'\
                             'Seattle', 'Secaucus', 'Saint Louis', 'Las Vegas'\
                             'Dallas', 'Los Angeles', 'New York']
    ca_city_server_groups = ['Vancouver', 'Montreal', 'Toronto']
    # au_city_server_groups = ['Melbourne', 'Sydney', 'Adelaide',\
    #                          'Brisbane', 'Perth']
    
    all_serves = us_city_server_groups + ca_city_server_groups #+ au_city_server_groups
    # all_serves = all_serves + ["United Kingdom"]
    
    group = random.choice(all_serves)
    
    # command = f'cd "C:\\Program Files\\NordVPN\\"; nordvpn -c -g "{group}"'
    command = f'nordvpn -c -g "{group}"'
    os.chdir("C:\\Program Files\\NordVPN\\")
    os.system(command)
    public_ip = current_ip
    start = datetime.now()
    for i in range(15):
        time.sleep(1)
        try:
            public_ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
        except:
            pass
        if public_ip != current_ip:
            print(f'Connected to {public_ip}\n')
            complete = datetime.now()
            print(f'It took {(complete - start).total_seconds()} seconds\n')
            os.chdir(current_path)
            return 0
    os.chdir(current_path)
    return connect_to_nord()

connect_to_nord()
# binary = webdriver.firefox.firefox_binary('S:/webdriver/geckodriver_win64/geckodriver.exe')
driver = webdriver.Firefox(executable_path=r'S:/webdriver/geckodriver_win64/geckodriver.exe')
driver.get("http://alta.registries.gov.ab.ca/SpinII/searchtitleradius.aspx")
# assert "Python" in driver.title
driver.implicitly_wait(60)
main_page = driver.current_window_handle

def close_popup (driver = driver, main_page = main_page):
    popup = driver.window_handles[driver.window_handles != main_page]
    driver.switch_to.window(popup)
    driver.close()
    driver.switch_to.window(main_page)
close_popup (driver, main_page)

# We need to login as guest first
g_login = driver.find_element_by_id("uctrlLogon_cmdLogonGuest")
g_login.click()

# Agree the disclamier
agree = driver.find_element_by_id("cmdYES")
agree.click()

# Navigate to the the search by radius page
driver.get("http://alta.registries.gov.ab.ca/SpinII/searchtitleradius.aspx");


def search_title(rad, linc, date, driver=driver):
    rad_search_elem = driver.find_element_by_id("TitleRadius_ctlRadius_txtRadius")
    rad_search_elem.clear()
    rad_search_elem.send_keys(rad)
    
    
    linc_search_elem = driver.find_element_by_id("TitleRadius_ctlLinc_txtLincNumber")
    linc_search_elem.clear()
    linc_search_elem.send_keys(linc)
    
    
    date_search_elem = driver.find_element_by_id("TitleRadius_ctlDateChange_txtDateChanged")
    date_search_elem.clear()
    date_search_elem.send_keys(date)
    date_search_elem.send_keys(Keys.RETURN)



def next_page_loaded(page, current_page, driver=driver, loop_count=0, patience=50):
    try:
        while current_page != page: 
            current_page = int(driver.find_element_by_id("TitleResult_lblPageNumber").text.split(' ')[1])
    except:
        loop_count = loop_count+1
        if loop_count<patience:
            next_page_loaded(page, current_page, loop_count=loop_count)
        else:
            print("Ran out of patience\n")
            print(f'current_page = {current_page} and page = {page}')
    return True

def scrape_results (out_obj = {}, linc_to_skip = [], driver=driver, backup = "backup.txt", backup_block = 10):
    page_selector = driver.find_element_by_id("TitleResult_ddPage")
    current_page = int(driver.find_element_by_id("TitleResult_lblPageNumber").text.split(' ')[1])
    total_page = int(driver.find_element_by_id("TitleResult_lblPageNumber").text.split(' ')[-1])
    search_results = int(driver.find_element_by_id("TitleResult_lblTotalResults").text.split(' ')[0])
    entry_processed = 0
    if "latest_page" not in out_obj:
        out_obj['latest_page'] = 1
        start_page = 1
    else:
        start_page = out_obj['latest_page']
        
    for page in range(start_page, total_page+1):
        out_obj['latest_page'] = page
        if page ==11:
            1==0
        if page != 1:
            # page_selector = driver.find_element_by_id("TitleResult_ddPage")
            # page_selector.send_keys(str(page))
            # page_selector = driver.find_element_by_id("TitleResult_ddPage")
            driver.find_element_by_xpath(f"//select[@id='TitleResult_ddPage']/option[text()='{page}']").click()
            current_page = int(driver.find_element_by_id("TitleResult_lblPageNumber").text.split(' ')[1])
            if next_page_loaded(page, current_page):
                pass

        max_i = 10
        if page == total_page:
            max_i = search_results % 10
        for i in range(max_i):
            time.sleep(0.2)
            linc = driver.find_element_by_id("TitleResult_dgResults_lblLINC_"+str(i)).text
            if (linc not in out_obj) and (linc not in linc_to_skip):
                out_obj[linc] = open_extract_title(i)
                if entry_processed%backup_block == 0:
                    with open(backup, 'w') as outfile:
                        json.dump(out_obj, outfile)
    return out_obj

def open_extract_title(i, driver=driver, main_page=main_page):
    base_info = {}
    base_info['LINC Number'] = driver.find_element_by_id("TitleResult_dgResults_lblLINC_"+str(i)).text
    base_info['Registration Date'] = driver.find_element_by_id("TitleResult_dgResults_lblRegDate_"+str(i)).text
    base_info['Change/Cancel Date'] = driver.find_element_by_id("TitleResult_dgResults_lblChangeDate_"+str(i)).text
    
    btn = driver.find_element_by_id("TitleResult_dgResults_cmdPreview_"+str(i))
    btn.click()
    title_page = driver.window_handles[driver.window_handles != main_page]
    driver.switch_to.window(title_page)
    title_preview = driver.find_elements_by_tag_name("pre")[0].text
    info = pharse_title_preview(title_preview)
    for key in base_info:
        info[key] = base_info[key]
    driver.close()
    driver.switch_to.window(main_page)
    return info

def pharse_title_preview(string):
    lines = string.split('\n')
    out_obj = {}
    out_obj['condominium'] = "CONDOMINIUM" in string
    reached_table = False
    for i in range( len(lines) ):
        if "LINC" in lines[i] and "SHORT LEGAL" in lines[i]:
            keys = list(filter(None, lines[i].split("  ")))
            content = list(filter(None, lines[i+1].split("  ")))
            for i in range(len(keys)):
                try:
                    keys[i] = keys[i].replace(" ","")
                    out_obj[keys[i]] = content[i].replace(" ","")
                except:
                    print("Something went wrong, the LINC line not matching")
        elif "PLAN" in lines[i]:
            out_obj["PLAN"] = lines[i].replace("PLAN", "").replace(" ", "")
        elif "BLOCK" in lines[i]:
            out_obj["BLOCK"] = lines[i].replace("BLOCK", "").replace(" ", "")
        elif "LOT" in lines[i]:
            out_obj["LOT"] = lines[i].replace("LOT", "").replace(" ", "")
        elif "EXCEPTING THEREOUT ALL MINES AND MINERALS" in lines[i]:
            out_obj["Surface Rights Only"] = True
        elif "ESTATE" in lines[i]:
            out_obj["ESTATE"] = lines[i].replace("ESTATE: ", "").replace("  ", "")
        elif "ATS REFERENCE" in lines[i]:
            out_obj["ATS REFERENCE"] = lines[i].replace("ATS REFERENCE:", "").replace(" ", "")
        elif "MUNICIPALITY" in lines[i]:
            out_obj["MUNICIPALITY"] = lines[i].replace("MUNICIPALITY: ", "")
        elif "REFERENCE NUMBER" in lines[i]:
            out_obj["REFERENCE NUMBER"] = lines[i].replace("REFERENCE NUMBER: ", "").replace(" ","")
        elif "DOCUMENT TYPE" in lines[i]:
            table_keys = list(filter(None, lines[i].split("  ")))
            table_keys = [k.replace(" ","") for k in table_keys]
            reached_table = True
            # out_obj['registration record'] = []
            # for key in table_keys:
            #     out_obj[key] = []
        
        if reached_table:
            # rec = {}
            table_content = list(filter(None, lines[i].split("  ")))
            if len(table_content) == len(table_keys) and table_content[0] != table_keys[0]:
                for i in range(len(table_keys)):
                    out_obj[table_keys[i]] = table_content[i].replace(" $","$")
                # out_obj['registration record'].append(rec)
            else:
                if any(char.isdigit() for char in lines[i]):
                    # rec['raw'] = lines[i]
                    # out_obj['registration record'].append(rec)
                    pass
    out_obj['raw'] = string
    return out_obj

# sample = 'S\nLINC             SHORT LEGAL                                   TITLE NUMBER\n0010 148 781     1485HW;6;N                                    002 289 184\n\nLEGAL DESCRIPTION\nPLAN 1485HW  \nBLOCK 6  \nLOT N  \nEXCEPTING THEREOUT ALL MINES AND MINERALS  \n  \nESTATE: FEE SIMPLE  \nATS REFERENCE: 4;24;52;20;SW\n\nMUNICIPALITY: CITY OF EDMONTON\n\nREFERENCE NUMBER: 972 092 840\n\n--------------------------------------------------------------------------------\n                         REGISTERED OWNER(S)\nREGISTRATION    DATE(DMY)  DOCUMENT TYPE      VALUE           CONSIDERATION\n--------------------------------------------------------------------------------\n\n002 289 184    02/10/2000  TRANSFER OF LAND   $146,000        $146,000'
# pharse_title_preview(sample)

# [{"LINC":"0030706105", "rad":10000, "date":"01/01/2012"},
#   {"LINC":"0037002920", "rad":10000, "date":"01/01/2012"},
#   {"LINC":"0016892077", "rad":10000, "date":"01/01/2012"},
#   {"LINC":"0029106200", "rad":10000, "date":"01/01/2012"}]
    
test_search = [{"LINC":"0016892077", "rad":10000, "date":"01/01/2012"},
                {"LINC":"0029106200", "rad":10000, "date":"01/01/2012"}]
# # test_search = [{"LINC":"0029106200", "rad":100, "date":"01/01/2012"}]
result = {}
# for search in test_search:
#     driver.implicitly_wait(5)
#     search_title(str(search['rad']), search['LINC'], search['date'])
#     driver.implicitly_wait(5)
#     result = scrape_results(out_obj = result)
#     driver.implicitly_wait(5)
def batch_search(search_arr, result_obj = {}):
    search = search_arr[0]
    if "latest_linc" not in result_obj:
        result_obj['latest_linc'] = search['LINC']
    else:
        if result_obj['latest_linc']!=search['LINC']:
            return batch_search(search_arr[1:], result_obj = result_obj)
    time.sleep(1)
    search_title(str(search['rad']), search['LINC'], search['date'])
    time.sleep(1)
    result_obj = scrape_results(out_obj = result_obj)
    
    if len(search_arr[1:]) >=1:
        time.sleep(2)
        result_obj['latest_linc'] = search_arr[1]['LINC']
        result_obj['latest_page'] = 1
        return batch_search(search_arr[1:], result_obj = result_obj)
    del result_obj['latest_linc']
    del result_obj['latest_page']
    return result_obj

def wrapper(search_arr, driver = driver):
    try:
        connect_to_nord()
        with open('backup.txt') as json_file:
            result = json.load(json_file)
            
        result = batch_search(search_arr, result)
    except:
        wrapper(search_arr, driver = driver)
    return result

result = wrapper(test_search)
with open(current_time+'.txt', 'w') as outfile:
    json.dump(result, outfile)

