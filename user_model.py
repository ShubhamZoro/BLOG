import mysql.connector
import os

mydb=mysql.connector.connect(host='localhost',user='root',password=f"{os.getenv('mysql_password')}",auth_plugin ='mysql_native_password')
print(mydb)

my_cursor=mydb.cursor()
my_cursor.execute("CREATE DATABASE users")
# my_cursor.execute("SHOW DATABASE")
# my_cursor.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY,email VARCHAR(255), password VARCHAR(255), name VARCHAR(255))")
# my_cursor.execute("CREATE TABLE users (id INT AUTO_INCREMENT PRIMARY KEY,email VARCHAR(255), password VARCHAR(255), name VARCHAR(255))")



# sql = "INSERT INTO users ( name, address,password,name) VALUES (%s, %s, %s, %s)"
# val = ("John", "Highway 21")
# my_cursor.execute(sql, val)
#
# mydb.commit()
#
# print(my_cursor.rowcount, "record inserted.")
#
# my_cursor.execute("SELECT * FROM users")
#
# myresult = my_cursor.fetchall()
#
# for x in myresult:
#   print(x)
