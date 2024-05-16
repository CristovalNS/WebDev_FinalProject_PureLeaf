from fastapi import FastAPI, HTTPException, Body
import requests
from login_pydantic import *
import mysql.connector
import firebase_admin
from mysql.connector import Error
from firebase_admin import credentials, auth, exceptions
import json

cred = credentials.Certificate('pureleaf-9d01f-firebase-adminsdk-fyu2u-356ec2f32c.json')
firebase_admin.initialize_app(cred)

app = FastAPI()


def create_mysql_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='*neoSQL01',
            database='central_database'
        )
        return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
    

# API Endpoints
# Register user
@app.post("/register")
def register_user(user: UserRegistration):
    connection = create_mysql_connection()
    if connection.is_connected():
        try:
            # Create user in Firebase
            user_record = auth.create_user(
                email=user.email,
                password=user.password
            )
            # Prepare a MySQL query
            query = "INSERT INTO user_account (user_id, email, user_type_id) VALUES (%s, %s, %s)"
            data = (user_record.uid, user.email, user.user_type)
            
            cursor = connection.cursor()
            cursor.execute(query, data)
            connection.commit()
            return {"uid": user_record.uid, "email": user.email, "user_type": user.user_type}
        except exceptions.FirebaseError as e:
            connection.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        except Error as e:
            connection.rollback()
            print("Failed to insert record into MySQL table {}".format(e))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    else:
        raise HTTPException(status_code=500, detail="Failed to connect to the database")


# Login user
@app.post("/login")
async def login(email: str = Body(...), password: str = Body(...)):
    # Firebase API endpoint for verifying email and password
    url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyDUFJFTNKv-LkGplr4-36MNOMXXj0wFL0Q"
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"email": email, "password": password, "returnSecureToken": True})
    
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        user_info = response.json()
        return {"uid": user_info['localId'], "email": user_info['email']}
    else:
        raise HTTPException(status_code=401, detail="Authentication failed")