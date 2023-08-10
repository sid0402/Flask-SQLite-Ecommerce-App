#IMPORTS
from flask import Flask, request, redirect, url_for
from datetime import datetime
import sqlite3
from datetime import datetime
import pandas as pd
import logging

#setting up logging information. file: "log.log"
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
logFormatStr = '[%(asctime)s] %(levelname)s - %(message)s'
formatter = logging.Formatter(logFormatStr,'%m-%d %H:%M:%S')
fileHandler = logging.FileHandler("log.log")
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(formatter)
app.logger.addHandler(fileHandler)

#creating inventort database through sqlite3
con = sqlite3.connect("inventory.db", check_same_thread=False)
app.logger.info("Connected to database")

#method of connecting to database
c = con.cursor()

#creating fields and their types in database
c.execute("""CREATE TABLE IF NOT EXISTS Inventory (
    SNo integer,
    Product text,
    Availability integer,
    Price integer
    )""")

#Inserting different products and its details into database
c.execute("""INSERT INTO Inventory VALUES 
    (1, "Pen", 5, 5), 
    (2, "Pencil", 5, 5), 
    (3, "Eraser", 5, 5), 
    (4,"Highlighter", 5, 5), 
    (5, "Sharpener", 5, 5)""")


con.commit()
app.logger.info("Database created")

#place that stores order information
cart = {"Serial Number": ["1", "2", "3", "4", "5"],"Item":["Pen","Pencil","Eraser","Highlighter","Sharpener"], "Quantity":0, "Price":0} #cart, including SNo, qty, price. Stores ordered information       
df = pd.DataFrame(cart)

#API to display products and their details
#Also gets user input abouyt what it wants to buy
@app.route("/products", methods = ["POST", "GET"])
def products():
    if request.method == "POST" or "GET":
        #have to do limit 5, otherwise multiple sets of the 5 products are chosen
        c.execute("SELECT * FROM Inventory LIMIT 5")
        #creates a variable that has fetched all information from the 5 products
        res = c.fetchall()
        app.logger.info("TABLE")
        app.logger.info(res)
        #creating dataframe to display product details to user - not used for anything else
        table_df = pd.DataFrame(res, columns=["Serial Number", "Item", "Items Left", "Price"])
        print("Welcome to this stationary website!")
        print(table_df) #displays all information to user
        con.commit()#saves changes to dataframe

        while (True):
            res = input("To add an item to your cart, type your answer in the format: SNo-Quantity. Type 6 to stop adding to cart\n")
            res = res.replace(" ", "").split("-")
            flag = int(res[0]) #serial number of current item
            if flag == 6: #user wants to quit ordering, user redirected to /list route
                break
            else:
                quant = int(res[1]) #quantity ordered for current item
                app.logger.info("User wants "+str(df["Item"][flag-1]) +" in quantity "+str(quant))
                #finding details of product ordered based on serial number of producd
                c.execute("SELECT * FROM Inventory where SNo = ?",(flag,))
                a = c.fetchone()
                items_left = int(a[2]) #number of items left of the current product ordered
                #validating user order by comparing items ordered by items left in database
                if quant > items_left: #if quantity ordered is greater than quantity available
                    print("Invalid order")
                    print("Available items for " + str(a[1]) + " are: " + str(items_left))
                else:
                    #updating quantity and price of order
                    df.iat[flag-1, 2] = quant
                    df.iat[flag-1, 3] = quant * 5
        return redirect(url_for("list"))

#API to show the items and sum of the order
#Redirects users to the buying page (if they want to proceed)
@app.route("/list", methods=["POST", "GET"])
def list():
    #df is the cart which stores the orders
    print(df)
    sum = int(df["Price"].sum()) #total price of order
    print("Total: " + str(sum))
    app.logger.info("Total: " + str(sum))
    #asking user if they want to proceed to /buy API or cancel order (no redirects)
    s = input("Do you want to proceed?")
    if (s.lower() == "yes"or"y"):
        app.logger.info("User wants to proceed to checkout")
        #redirects to buy API
        return redirect(url_for("buy"))
    else:
        app.logger.info("User cancelled the order")
        return "Order cancelled"

#User to actually buy the order and remove the items from the database
@app.route("/buy", methods=["POST", "GET"])
def buy():
    s = input("Do you want to buy?")
    if (s.lower() == "yes"or"y"): #user wants to buy items
        app.logger.info("User wants to buy items")
        #Updating database by subtracting quantity
        for i in range(1,6):
            quant = int(df.iat[i-1,2]) #finding quantity ordered for each item
            c.execute("SELECT * FROM Inventory WHERE SNo =?", (i,))
            a = c.fetchone()
            quant_left = int(a[2])
            #subtracting quantity ordered from quantity available
            new_quant = quant_left - quant
            c.execute("UPDATE Inventory set Availability = ? WHERE SNo = ?",(new_quant,i))
            con.commit()
        print("UPDATED DATABASE")
        #fetching data after database has been updated. it will be used for logging and printing.
        c.execute("SELECT * FROM Inventory LIMIT 5")
        res = c.fetchall()
        print(pd.DataFrame(res))
        app.logger.info("UPDATED DATABASE")
        app.logger.info(res)
        #logs and prints the purchased items
        print("Successfully Purhcased Items:")
        print(df.loc[lambda df: df["Quantity"] != 0])
        return_df = df.loc[lambda df: df["Quantity"] != 0]
        app.logger.info("FINAL ITEMS ORDERED")
        app.logger.info(df.loc[lambda df: df["Quantity"] != 0])
    return return_df.to_string()

#to log the time at which the user logged in
now = datetime.now() 
dt_string = now.strftime("%d-%m-%Y-%H-%M-%S")
app.logger.info("User logged in at: "+dt_string)

if __name__ == "__main__":
    app.run(debug=True)