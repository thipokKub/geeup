__copyright__ = """
    Copyright 2019 Samapriya Roy
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
__license__ = "Apache 2.0"

import requests
import ast
import ee
import sys
from pathlib import Path
from fnmatch import filter
from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from requests_toolbelt import MultipartEncoder
import time, os, getpass, subprocess
lp=os.path.dirname(os.path.realpath(__file__))
sys.path.append(lp)

def table_exist(path):
    return True if ee.data.getInfo(path) else False

def folder_exist(path):
    if ee.data.getInfo(path) and ee.data.getInfo(path)['type'].lower() == 'folder':
        return True
    else:
        return False


def create_image_collection(full_path_to_collection):
    if folder_exist(full_path_to_collection):
        print(F"Folder {str(full_path_to_collection)} already exists")
    else:
        ee.data.createAsset({'type': ee.data.ASSET_TYPE_FOLDER}, full_path_to_collection)
        print(F"New folder {str(full_path_to_collection)} created")

def seltabup(dirc, uname, destination, passw=None):
    ee.Initialize()
    options = Options()
    options.add_argument('-headless')
    authorization_url="https://code.earthengine.google.com"
    
    fp = webdriver.FirefoxProfile()
    fp.set_preference("browser.download.folderList",2)
    fp.set_preference("browser.download.manager.showWhenStarting",False)  
    fp.set_preference("browser.download.dir","/home")
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/plain,application/x-powerpoint")

    if passw is None:
        passw = getpass.getpass()
    create_image_collection(destination)
    if os.name=="nt":
        driver = Firefox(executable_path=os.path.join(lp,"geckodriver.exe"), firefox_options=options, firefox_profile=fp)
    else:
        driver = Firefox(executable_path=os.path.join(lp,"geckodriver"), firefox_options=options, firefox_profile=fp)
    driver.get(authorization_url)
    time.sleep(5)
    username = driver.find_element_by_xpath('//*[@id="identifierId"]')
    username.send_keys(uname)
    driver.find_element_by_id("identifierNext").click()
    time.sleep(5)

    passw=driver.find_element_by_name("password").send_keys(passw)
    driver.find_element_by_id("passwordNext").click()
    time.sleep(5)

    try:
        driver.find_element_by_xpath("//div[@id='view_container']/form/div[2]/div/div/div/ul/li/div/div[2]/p").click()
        time.sleep(5)
        driver.find_element_by_xpath("//div[@id='submit_approve_access']/content/span").click()
        time.sleep(5)
    except Exception as e:
        pass

    cookies = driver.get_cookies()

    s = requests.Session()
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    driver.close()
    try:
        valid_items = sorted(list(filter(list(map(lambda x: str(x), Path(dirc).rglob(F'*') )), "*.[Zz][Ii][Pp]")))
        
        for index, item in enumerate(valid_items):
            f_name = "-".join(os.path.basename(item).split('.')[:-1]) 
            dest_full_path = os.path.join(destination, f_name)

            if table_exist(dest_full_path):
                print(F'Table already exists Skipping: {str(fpath)}')
            else:
                r = s.get("https://code.earthengine.google.com/assets/upload/geturl")
                d = ast.literal_eval(r.text)
                upload_url = d['url']

                with open(item, 'rb') as f:
                    upload_url = d['url']
                    try:
                        m = MultipartEncoder( fields={'zip_file': (F"{f_name}.zip", f)})
                        resp = s.post(upload_url, data=m, headers={'Content-Type': m.content_type})
                        gsid = resp.json()[0]

                        output = subprocess.check_output(F"earthengine --no-use_cloud_api upload table --asset_id {str(dest_full_path)} {str(gsid)}", shell=True)
                        print(F"Ingesting {str(index + 1)} of {len(valid_items)} { f_name } task ID: {(output.decode('utf-8')).strip()}")
                    except Exception as e:
                        print(e)
    except Exception as e:
        print(e)
