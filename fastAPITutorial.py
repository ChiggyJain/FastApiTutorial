
# importing different types of modules as per requirement
from fastapi import FastAPI
from fastapi import Path
from fastapi import Query
from fastapi import Form
from fastapi import UploadFile
from fastapi import File
from openpyxl.workbook import Workbook
from pydantic import BaseModel
from fastapi import Request
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Cookie
from typing import List
from fastapi import Depends
import aiomysql
import boto3
from sympy.physics.units import seconds
from sympy.plotting.intervalmath import interval
from twilio.rest import Client
import os
import bcrypt
import csv
import io
from openpyxl import Workbook
from fastapi.responses import StreamingResponse
from io import BytesIO
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
from google.oauth2 import service_account
import json
from fastapi.responses import FileResponse
from dataclasses import field

# app configuration
app = FastAPI(swagger_ui_parameters={"syntaxHighlight":False})

### static files and templates loading concept
app.mount("/static", StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")

# aws s3 bucket credentials
awsAccessKeyID = "AKIAQM7VXCBETRKYJT6B"
awsSecretKey = "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"
awsRegionName = "ap-northeast-1"
awsS3BucketName = "uploadimages12"

# twilio sms config credentials
twilioAccountId = "ACbae4e8ba853965aeaaae1b3477f53e47"
twilioAccountAuthToken = "f865d78ff4fd796a424092994cdfa107"
twilioSenderPhoneNo = "+18315083381"

# twilio whatsapp config credentials
twilioAccountId = "ACbae4e8ba853965aeaaae1b3477f53e47"
twilioAccountAuthToken = "f865d78ff4fd796a424092994cdfa107"
twilioSenderWhatsAppPhoneNo = "+14155238886"

# openweather api credentials
openWeatherApiKey = "7fc886543f9f1e0b36d45b2d03d88e78"
openWeatherApiBaseUrl = "https://api.openweathermap.org/data/2.5/weather"

# smtp email sending credentials
smtpSenderEmailID = "cjain9975@gmail.com"
smtpSenderEmailPwd = "kbaayuggcrmvruys"

# fcm credentials
fcmServiceAccountFile = "credentials/cj-fastapi-push-ntf-firebase-adminsdk-fbsvc-b82f740804.json"
fcmScopes = ["https://www.googleapis.com/auth/firebase.messaging"]
credentials = service_account.Credentials.from_service_account_file(
    fcmServiceAccountFile, scopes=fcmScopes
)
fcmUrl = "https://fcm.googleapis.com/v1/projects/cj-fastapi-push-ntf/messages:send"

# initialize the scheduler
scheduler = AsyncIOScheduler()

# getting db connection details
async def getMysqlDbConnectionDetails():
    async with aiomysql.connect(
        host="localhost",
        user="dgdb",
        password="c",
        db="FASTAPI_TUTORIAL"
    ) as dbConn: yield dbConn

# generating hashing string
def genBcryptHashString(gvnStr):
    saltKey = bcrypt.gensalt()
    hashedStr = bcrypt.hashpw(gvnStr.encode("utf-8"), saltKey)
    return hashedStr.decode("utf-8")

# sending email via smtp
def sendSingleEmailViaSmtp(emailTemplate):
    ### preparing msg template
    msgObj = MIMEMultipart()
    msgObj["From"] = smtpSenderEmailID
    msgObj["To"] = emailTemplate.to
    msgObj["Subject"] = emailTemplate.subject
    msgObj.attach(MIMEText(emailTemplate.body, "plain"))
    ### connecting to smtp server
    svrObj = smtplib.SMTP("smtp.gmail.com", 587)
    svrObj.starttls()
    svrObj.login(smtpSenderEmailID, smtpSenderEmailPwd)
    svrObj.sendmail(smtpSenderEmailID, emailTemplate.to, msgObj.as_string())
    svrObj.quit()
    return "Sent Email Successfully"

# getting fcm token
def getFcmToken():
    from google.auth.transport.requests import Request
    credentials.refresh(Request())
    token = credentials.token
    return token



# example: push notification via FCM
@app.get("/firebase-messaging-sw.js")
async def service_worker():
    from fastapi.responses import FileResponse
    return FileResponse("firebase-messaging-sw.js")
class PushNotificationFieldTemplateModel(BaseModel):
    title:str
    body:str
    deviceToken:str
@app.post("/sendPushNotificationViaFCM/", response_model=None)
async def sendPushNotificationViaFCM(Template:PushNotificationFieldTemplateModel):
    message = {
      "message": {
        "token": Template.deviceToken,
        "notification": {
          "title": Template.title,
          "body": Template.body + ". This will show automatically if app is in background."
        },
        "data": {
          "title": Template.title,
          "body": Template.body+ ". This will be handled in foreground and service worker.",
          "click_action": "https://youtube.com"
        },
        "webpush": {  # Important for browser background
          "headers": {
              "Urgency": "high"
          },
          "notification": {
              "title": Template.title,
              "body": Template.body,
              "icon": "/static/icon.png",
              "click_action": "https://youtube.com"
          }
        }
      }
    }
    headers = {
        "Authorization": f"Bearer {getFcmToken()}",
        "Content-Type": "application/json; UTF-8",
    }
    response = requests.post(fcmUrl, headers=headers, data=json.dumps(message))
    print(response.status_code, response.text)
    return "Push notification sent successfully"


@app.get("/subscribePushNotification/")
async def subscribePushNotification():
    return FileResponse("templates/subscribe_push_ntf.html")




'''
async def myScheduleTask1():
    print("Executing my task1")
@app.on_event("startup")
async def startScheduler():
    scheduler.add_job(myScheduleTask1, "interval", seconds=10)
    scheduler.start()
'''

# example: sending bulk email via smtp through background-task
class EmailFieldTemplateModel(BaseModel):
    to:str
    subject:str
    body:str
class EmailRequest(BaseModel):
    email:List[EmailFieldTemplateModel]
@app.post("/sendBulkEmailInBackgroundViaSmtp/")
async def sendBulkEmailInBackgroundViaSmtp(emails:List[EmailRequest], backgroundTask:BackgroundTasks):
    for req in emails:
        for eachEmailFieldTemplate in req.email:
            backgroundTask.add_task(sendSingleEmailViaSmtp, eachEmailFieldTemplate)
    return "Email will be send in background system"


# example: sending email on spot via smtp
@app.post("/sendEmailOnSpotViaSmtp/")
async def sendEmailOnSpotViaSmtp(to:str, subject:str, body:str):
    ### preparing msg template
    msgObj = MIMEMultipart()
    msgObj["From"] = smtpSenderEmailID
    msgObj["To"] = to
    msgObj["Subject"] = subject
    msgObj.attach(MIMEText(body, "plain"))
    ### connecting to smtp server
    svrObj = smtplib.SMTP("smtp.gmail.com", 587)
    svrObj.starttls()
    svrObj.login(smtpSenderEmailID, smtpSenderEmailPwd)
    svrObj.sendmail(smtpSenderEmailID, to, msgObj.as_string())
    svrObj.quit()
    return "Email sent successfully"

# example: get current weather details from third party api
@app.get("/getCurrentWeatherDetails/")
async def createExcelsheetFile(city:str):
    paramObj = {"q":city, "aapid":openWeatherApiKey, "units":"metric"}
    async with httpx.AsyncClient() as client:
        response = await client.get(openWeatherApiBaseUrl, params=paramObj)
        # response = await client.get(f"https://api.openweathermap.org/data/2.0/weather?lat=44.34&lon=10.99&appid={openWeatherApiKey}")
        return response.json()


# example: creating excelsheet file
@app.post("/createExcelsheetFile/")
async def createExcelsheetFile():
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "101"])
    ws.append(["Name", "Chirag"])
    excelIO = BytesIO()
    wb.save(excelIO)
    excelIO.seek(0)

    return StreamingResponse(
        BytesIO(excelIO.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={'Content-Disposition':'attachment;filename="example.xlsx"'}
    )


# example: write csv file
class csvDataModel(BaseModel):
    id:int
    first_name:str
class CsvRequestModel(BaseModel):
    data:List[csvDataModel]
    file_name:str
@app.post("/writeCsvFile/")
async def writeCsvFile(csvRequestData:CsvRequestModel):
    if csvRequestData.file_name.endswith(".csv"):
        with open(os.path.join("uploads")+"/"+csvRequestData.file_name, 'a', newline='') as fObj:
            colNamesList = ["id","first_name"]
            writer = csv.DictWriter(fObj, fieldnames=colNamesList)
            if fObj.tell() == 0:
               writer.writeheader()
            for eachRow in csvRequestData.data:
                writer.writerow(eachRow.model_dump())
        # return readCsvFile(csvRequestData.file_name)
        return "Success"
    else:
        return "Csv file only allowed"

# example: read csv file
@app.post("/readCsvFile/")
async def readCsvFile(file_name:str):
    if file_name.endswith(".csv"):
        with open(os.path.join("uploads")+"/"+file_name) as fObj:
            csvReader = csv.DictReader(fObj)
            jsonData = [eachRow for eachRow in csvReader]
            return jsonData
    else:
        return "Csv file only allowed"

# example: upload csv file
@app.post("/uploadCsvFile/")
async def uploadCsvFile(file:UploadFile=File(...)):
    if file.filename.endswith(".csv"):
       fileContents = await file.read()
       csvData = io.StringIO(fileContents.decode("utf-8"))
       csvReader = csv.DictReader(csvData)
       jsonData = [eachRow for eachRow in csvReader]
       return jsonData
    else:
        return "Csv file only allowed"

# example: get hash-string via bcrypt
@app.get("/getHashStringViaBcrypt/")
async def getHashStringViaBcrypt(givenStr:str):
    return genBcryptHashString(givenStr)


# example: verify-otp-msg via twilio
@app.post("/verifySmsOTP/")
async def verifySmsOTP(otp:str):
    if otp == "123456":
       return "Matched"
    return "Not Match"

# example: send-otp-msg via twilio
@app.post("/sendSmsOTPViaTwilio/")
async def sendSmsOTPViaTwilio(to:str):
    client = Client(twilioAccountId, twilioAccountAuthToken)
    twilioConObj = client.messages.create(
        to=to,
        from_=twilioSenderPhoneNo,
        body="Your OTP:123456"
    )
    return {"Sent-SMSOTP-MsgID:", twilioConObj.sid}


# example: send-whatsapp-msg via twilio
@app.post("/sendWhatsAppViaTwilio/")
async def sendWhatsAppViaTwilio(to:str, body:str):
    client = Client(twilioAccountId, twilioAccountAuthToken)
    twilioConObj = client.messages.create(
        to="whatsapp:+919975967186",
        from_="whatsapp:"+twilioSenderWhatsAppPhoneNo,
        body=body
    )
    return {"WhatsApp-MsgID:", twilioConObj.sid}


# example: send-sms via twilio
@app.post("/sendSmsViaTwilio/")
async def sendSmsViaTwilio(to:str, body:str):
    client = Client(twilioAccountId, twilioAccountAuthToken)
    twilioConObj = client.messages.create(
        to="+919975967186",
        from_=twilioSenderPhoneNo,
        body=body
    )
    return {"Sms-MsgID:", twilioConObj.sid}

# example: upload image into aws s3 bucket
@app.post("/uploadImageAwsS3Bucket/")
async def uploadImageAwsS3Bucket(fileParam:UploadFile=File(...)):
    awsS3ClientObj = boto3.client(
        's3',
        aws_access_key_id = awsAccessKeyID,
        aws_secret_access_key = awsSecretKey,
        region_name = awsRegionName
    )
    awsS3ClientObj.upload_fileobj(
        fileParam.file,
        awsS3BucketName,
        fileParam.filename
    )
    imgUrl = f"https://{awsS3BucketName}.s3.{awsRegionName}.amazonaws.com/{fileParam.filename}"
    return imgUrl


# example: deleting single user details from mysql db table with dependency concept
@app.delete("/deleteSingleUsrDetailsIntoMysqlDB/{usr_id}")
async def deleteSingleUsrDetailsIntoMysqlDB(usr_id:int, dbConn=Depends(getMysqlDbConnectionDetails)):
    async with dbConn.cursor() as cur:
        await cur.execute(
            "DELETE FROM USER WHERE 1 AND id=%s",
            usr_id
        )
        await dbConn.commit()
        return await getAllUsrDetailsFrmMysqlDB(dbConn)

# example: updating single user details from mysql db table with dependency concept
@app.put("/updateSingleUsrDetailsIntoMysqlDB/{usr_id}")
async def updateSingleUsrDetailsIntoMysqlDB(usr_id:int, first_name:str, dbConn=Depends(getMysqlDbConnectionDetails)):
    async with dbConn.cursor() as cur:
        await cur.execute(
            "UPDATE USER SET first_name=%s WHERE 1 AND id=%s",
            (first_name, usr_id)
        )
        await dbConn.commit()
        return await getSingleUsrDetailsFrmMysqlDB(usr_id, dbConn)

# example: getting single user details from mysql db table with dependency concept
@app.get("/getSingleUsrDetailsFrmMysqlDB/{usr_id}")
async def getSingleUsrDetailsFrmMysqlDB(usr_id:int, dbConn=Depends(getMysqlDbConnectionDetails)):
    async with dbConn.cursor() as cur:
        await cur.execute("SELECT * FROM USER WHERE 1 AND id=%s", usr_id)
        records = await cur.fetchone()
        if not records:
           return "No user details is found"
        return records

# example: getting all user details from mysql db table with dependency concept
@app.get("/getAllUsrDetailsFrmMysqlDB")
async def getAllUsrDetailsFrmMysqlDB(dbConn=Depends(getMysqlDbConnectionDetails)):
    async with dbConn.cursor() as cur:
        await cur.execute("SELECT * FROM USER")
        return await cur.fetchall()

# example: dumping single user details into mysql db table with dependency concept
class SingleUsrModel(BaseModel):
    first_name:str
@app.post("/createSingleUsrDetailsInMysqlDB")
async def createSingleUsrDetailsInMysqlDB(usrObj:SingleUsrModel, dbConn=Depends(getMysqlDbConnectionDetails)):
    async with dbConn.cursor() as cur:
        await cur.execute(
            "INSERT INTO USER (first_name) VALUES (%s)",
            (usrObj.first_name)
        )
        lastInsertedUsrId = cur.lastrowid
        await dbConn.commit()
        return {"message":"User details is added successfully", "ID":lastInsertedUsrId}


# example: dependency injection
def getFakeDbConnectionDetails():
    return "Fake DB Connection Details"
def getFakeLoggedInUsrDetails():
    return "LoggedIn User Details"
@app.get("/getDependencyInjectionSampleDetails")
async def getDependencyInjectionSampleDetails(db:str=Depends(getFakeDbConnectionDetails), usr:str=Depends(getFakeLoggedInUsrDetails)):
    return {"db":db, "usr":usr}


# example: response nested model format data structure
class Address(BaseModel):
    country:str
    state:str
    city:str
    pincode:str
class Person(BaseModel):
    pName:str
    address:Address
class Company(BaseModel):
    cName:str
    employees:List[Person]
@app.post("/createCompanyEmployeeDetails", response_model=Company)
async def createCompanyEmployeeDetails(company:Company):
    return company


# example: response model format data structure
# pydantic model class of item-response sample data
class ItemResponseModel(BaseModel):
    id:int
    itemName:str
@app.get("/getItemResponseModel/{item_id}", response_model=ItemResponseModel)
async def getItemResponseModel(item_id:int):
    return {"id":1, "itemName":"Pizza"}

# example: get cookie
@app.post("/getCookieSample/")
async def getCookieSample(request: Request):
    cookieData = request.cookies.get('cookie1')
    return {"message":"Cookie data is extracted successfully", "extractedCookieData":cookieData}

# example: set cookie
@app.post("/setCookieSample/")
async def setCookieSample(response: Response):
    response.set_cookie(key="cookie1", value='CJ')
    return {"message":"Cookie is set successfully"}

# example: loading html template using jinja2 concept
@app.post("/submitHtmlElementForm/")
async def submitHtmlElementForm(username:str=Form(...)):
    return {"message":"Form is submitted successfully", "username":username}

@app.get("/showHtmlFormTemplate/", response_class=HTMLResponse)
async def showHtmlFormTemplate(request: Request):
    return templates.TemplateResponse("form.html", {"request":request})

# example: loading html template using jinja2 concept
@app.get("/loadIndexHtmlTemplate/", response_class=HTMLResponse)
async def loadIndexHtmlTemplate(request: Request):
    return templates.TemplateResponse("index.html", {"request":request, "title" : "FastAPI Templates", "bodyMsg" : "FastAPI Templates"})

# example: uploading file sample
@app.post("/uploadFile/")
async def uploadFile(fileParam:UploadFile=File(...)):
    fileUploadDir = "uploads"
    os.makedirs(fileUploadDir, exist_ok=True)
    filePath = os.path.join(fileUploadDir, fileParam.filename)
    with open(filePath, "wb") as fileObj:
        fileObj.write(await fileParam.read())
    return {"message":"File uploaded successfully", "fileName":fileParam.filename, "fileType":fileParam.content_type}

# example: submit form sample
@app.post("/submitForm1/")
async def submitForm1(userName:str=Form(...), pwd:str=Form(...)):
    return {"message":"Form submitted successfully", "Username":userName}

# example: url query parameters validation
@app.get("/itemQueryParametersValidation/")
async def itemQueryParametersValidation(item_name:str = Query(None, min_length=3, max_length=50)):
    return item_name

# example: url path parameters validation
@app.get("/itemPathParametersValidation/{item_id}")
async def itemPathParametersValidation(item_id:int = Path(..., title="The ID of the item to get details", ge=1)):
    return item_id

# example: creating item with pydantic model validation concept
# pydantic model class of item sample data
class Item(BaseModel):
    item_name:str
    item_price:float
    is_offer:bool=None
@app.post("/createItems/")
async def createItems(items:Item):
    return items

# example: url path+query parameters with datatypes
@app.get("/itemPathQueryParametersBothTogether/{item_id}")
async def readItemPathQueryParametersBothTogether(item_id:int, item_name:str=None):
    return {"item_id":item_id, "item_name":item_name}

# example: url query parameters with datatypes
@app.get("/itemQueryParameters/")
async def readItemQueryParameters(item_id:int, item_name:str=None):
    return {"item_id":item_id, "item_name":item_name}

# example: url path parameters with datatypes
@app.get("/itemPathParameters/{item_id}")
async def readItemPathParameters(item_id:int):
    return {"item_id":item_id}

# example: Helloworld
@app.get("/")
async def root():
    return {"message":"Hello World FastAPI!"}
