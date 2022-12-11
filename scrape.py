from bs4 import BeautifulSoup
import requests
from cs50 import SQL

db = SQL("sqlite:///beamCalc.db")

def get_tube_properties():
    hollow_tube_url = "http://www.b2bmetal.eu/en/pages/index/index/id/95/"

    response = requests.get(hollow_tube_url)

    website_html = response.text

    soup = BeautifulSoup(website_html, "html.parser")

    table = soup.select(selector=".table-list tbody tr")

    counter = 0
    for row in table:
        counter +=1
        # Tek od trećeg reda idu vrijednosti
        if counter < 3  or (counter > 65 and counter < 68):
            continue
        elif counter == 139:
            break

        print(f"row {counter}: {row.getText()}")

        d = round(float(row.getText().split(' ')[0].replace(",", ".").strip()), 1)
        t = round(float(row.getText().split(' ')[1].replace(",", ".").strip()), 1)
        A = round(float(row.getText().split(' ')[3].replace(",", ".").strip()) * 100, 1)
        Wx = round(float(row.getText().split(' ')[6].replace(",", ".").strip()) * 1000, 1)
        Wo = round(float(row.getText().split(' ')[10].replace(",", ".").strip()) * 1000, 1)

        print(f"d = {d} t = {t}, A = {A}, Wx = {Wx}, Wo = {Wo}")

        db.execute("INSERT INTO tube_section (diameter, thickness, area, Wx, Wo) VALUES (?,?,?,?,?);", d, t, A, Wx, Wo)
        
        if counter == 138:
            break

def get_squareHollow_properties():
    
    hollow_square_url = "http://www.b2bmetal.eu/en/pages/index/index/id/65/"

    response = requests.get(hollow_square_url)

    website_html = response.text

    soup = BeautifulSoup(website_html, "html.parser")

    table = soup.select(selector=".table-list tbody tr")

    counter = 0
    for row in table:
        counter +=1
        # Tek od trećeg reda idu vrijednosti
        if counter < 5  or (counter > 58 and counter < 63):
            continue
        elif counter == 116:
            break

        data = row.getText().strip().replace("\n", " ").replace("  ", " ").split(' ')

        a = round(float(data[0].replace(",", ".")), 1)
        t = round(float(data[1].replace(",", ".")), 1)
        A = round(float(data[5].replace(",", ".")) * 100, 1)
        Wx = round(float(data[8].replace(",", ".")) * 1000, 1)

        db.execute("INSERT INTO hollowSquare_section (side, thickness, area, Wx) VALUES (?,?,?,?);", a, t, A, Wx)
        
def get_rectangleHollow_properties():
    
    hollow_rectangle_url = "http://www.b2bmetal.eu/en/pages/index/index/id/94/"

    response = requests.get(hollow_rectangle_url)

    website_html = response.text

    soup = BeautifulSoup(website_html, "html.parser")

    table = soup.select(selector=".table-list tbody tr")

    counter = 0
    for row in table:
        counter +=1
        # Tek od trećeg reda idu vrijednosti
        if counter < 3 or (counter > 75 and counter < 78) or (counter > 173 and counter < 176):
            continue
        elif counter == 252:
            break

        data = row.getText().strip().replace("\n", " ").replace("  ", " ").split(' ')
        
        h = round(float(data[0].replace(",", ".")), 1)
        b = round(float(data[1].replace(",", ".")), 1)
        t = round(float(data[2].replace(",", ".")), 1)
        A = round(float(data[4].replace(",", ".")) * 100, 1)
        Wx = round(float(data[7].replace(",", ".")) * 1000, 1)

        print(f"{counter}: h = {h}, b = {b}, t = {t}, A = {A}, Wx = {Wx}")

        db.execute("INSERT INTO hollowRectangle_section (height, width, thickness, area, Wx) VALUES (?,?,?,?,?);", h, b, t, A, Wx)
        

get_rectangleHollow_properties()