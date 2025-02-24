from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import os

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--remote-debugging-port=9222")

start_point = "서울기술교육센터"
url = f"https://m.map.naver.com/search2/search.naver?query=%EC%84%9C%EC%9A%B8%EA%B8%B0%EC%88%A0%EA%B5%90%EC%9C%A1%EC%84%BC%ED%84%B0&sm=hty&style=v5"
driver = wb.Chrome(options=chrome_options)
driver.get(url)

# Wait until the iframe is available and switch to it
wait = WebDriverWait(driver, 20)  # Increased wait time
try:
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "searchIframe")))
except:
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Number of iframes on the page: {len(frames)}")
    for frame in frames:
        print(frame.get_attribute("name"))
    print("Error: searchIframe not found")
    driver.quit()
    exit(1)

# Continue with the rest of your script...
time.sleep(3)  # Increased wait time

Advertisement = driver.find_elements(By.CSS_SELECTOR, '.YwYLL')
data = driver.find_elements(By.CLASS_NAME, "item_tit _title")

print(f"Advertisement elements found: {len(Advertisement)}")
print(f"Data elements found: {len(data)}")

if len(data) > len(Advertisement):
    start_point_name = data[len(Advertisement)]
    start_point_name.click()
else:
    print("Error: Not enough elements found in 'data'")
    driver.quit()
    exit(1)

time.sleep(0.5)
start_point_name.click()
time.sleep(0.5)
driver.back()

# Check if the element exists before interacting with it
try:
    shop = driver.find_element(By.CLASS_NAME, "bubble_keyword_text")
    shop.click()
    time.sleep(2)
    driver.switch_to.default_content()
    driver.switch_to.frame("searchIframe")
except wb.common.exceptions.NoSuchElementException:
    print("Error: Element with class name 'bubble_keyword_text' not found")
    driver.quit()
    exit(1)

body = driver.find_element(By.CLASS_NAME, "Ryr1F")
shop_name = []
stars = []
addresses = []
categories = []
src = []

while True:
    last_height = driver.execute_script("return arguments[0].scrollHeight", body)
    driver.execute_script("arguments[0].scrollTop += 1200;", body)
    time.sleep(1)
    new_height = driver.execute_script("return arguments[0].scrollHeight", body)
    if new_height == last_height:
        break
    last_height = new_height

data = driver.find_elements(By.XPATH, '//*[@id="_pcmap_list_scroll_container"]/ul/li/div[1]/a[1]/div/div/span[1]')
button = driver.find_element(By.XPATH, '//*[@id="app-root"]/div/div[2]/div[2]/a[7]')

while True:
    i = 0
    while True:
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame("searchIframe")
            data = driver.find_elements(By.CLASS_NAME, "TYaxT")
            if i >= len(data):
                break
            shop_name.append(data[i].text)
            data[i].click()
            time.sleep(2)
            driver.switch_to.default_content()
            driver.switch_to.frame("entryIframe")
            address = driver.find_element(By.CLASS_NAME, "LDgIH")
            addresses.append(address.text)
            category = driver.find_element(By.CLASS_NAME, "lnJFt")
            categories.append(category.text.split(','))
            try:
                src.append(driver.find_element(By.XPATH, '//*[@id="ibu_1"]').get_attribute("src"))
            except:
                src.append('')
            try:
                stars.append(driver.find_elements(By.CSS_SELECTOR, ".LXIwF")[0].text.split("\n")[1])
            except:
                stars.append('0')
            i += 1
        except:
            break
    if button.get_attribute("aria-disabled") == "false":
        driver.switch_to.default_content()
        driver.switch_to.frame("searchIframe")
        button.click()
        time.sleep(3)
    else:
        break

import csv
with open("shop.csv", "w", newline="", encoding="CP949") as file:
    writer = csv.writer(file)
    header = ["상호명", "별점", "주소", "카테고리", "이미지"]
    writer.writerow(header)
    for i in range(len(shop_name)):
        writer.writerow([shop_name[i], stars[i], addresses[i], categories[i], src[i]])

import pandas as pd
df = pd.read_csv("shop.csv", encoding="CP949")
for i in range(len(df)):
    if df["주소"][i] == "서울 강서구 내발산동 강서로 289":
        df["주소"][i] = "내발산동 701-9"

import geopy.distance
distance = []
for i in range(len(df)):
    address = df["주소"][i]
    url = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={address}'
    headers = {
        "X-NCP-APIGW-API-KEY-ID": os.getenv("NAVERMAP_API_KEY_ID"),
        "X-NCP-APIGW-API-KEY": os.getenv("NAVERMAP_API_KEY")
    }
    data = requests.get(url, headers=headers).json()
    x = data["addresses"][0]['x']
    y = data["addresses"][0]['y']
    dis = geopy.distance.distance((37.5423051, 126.8412894), (y, x)).km
    dis = round(dis * 1000, 0)
    distance.append(int(dis))

df["거리"] = distance
df.to_csv("shop_distance.csv", encoding="CP949")

driver.quit()
