# views.py

from fastapi import HTTPException, FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel

from database import SessionLocal, engine
from models import Account, Destination
import requests
import jwt
# from . import models

router = FastAPI()
# models.Base.metadata.create_all(bind=engine)
# Account Model

class Account_check(BaseModel):
    email: str
    account_id: str
    account_name: str
    website: str = None

# Destination Model
class Destination_check(BaseModel):
    url: str
    http_method: str
    headers: dict

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/accounts")
def create_account(account: Account_check, db: Session = Depends(get_db)):
    #db_account = db.query(Account).filter((Account.email == account.email ,Account.account_id==Account.account_id)).first()
    db_account = db.query(Account).filter(or_(Account.email == account.email, Account.account_id == account.account_id)).first()
    if db_account:
        raise HTTPException(status_code=400, detail="Account already exists change your mail ID or account")
    # creation of onetime jwt token
    encoded_jwt = jwt.encode({"account_id": account.account_id}, "secret", algorithm="HS256")
    app_secret_token = encoded_jwt
    # Create an instance of the Account model using the data from Account_check
    new_account = Account(email=account.email, account_id=account.account_id, account_name=account.account_name, app_secret_token=app_secret_token, website=account.website)
    
    db.add(new_account)  # Add the new_account instance to the session
    db.commit()
    db.refresh(new_account)
    return {
        "message": "Account created successfully. Save your token for any manipulation further.",
        "api_token": new_account.app_secret_token
    }

@router.get("/accounts")
def get_account(app_secret_token: str, db: Session = Depends(get_db)):
    if not app_secret_token:
        return HTTPException(status_code=404, detail="Token Doesn't exist.")
    # fetching details using token
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token['account_id']
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or token is wrong.")
    return account

from fastapi import HTTPException

@router.put("/accounts")
def update_account(app_secret_token: str, account: Account_check, db: Session = Depends(get_db)):
    if not app_secret_token:
        raise HTTPException(status_code=404, detail="Token Doesn't exist.")

    # Decode the JWT token to get the account_id
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token.get('account_id')

    # Retrieve the account from the database based on the account_id
    db_account = db.query(Account).filter(Account.account_id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if the new values are different from the existing ones
    if db_account.email == account.email and \
       db_account.account_name == account.account_name and \
       db_account.website == account.website:
        raise HTTPException(status_code=400, detail="No changes detected. Nothing to update.")

    # Update the account with the new values
    if db_account.email != account.email:
        db_account.email = account.email
    if db_account.account_name != account.account_name:
        db_account.account_name = account.account_name
    if db_account.website != account.website:
        db_account.website = account.website
    db.commit()

    return {"message": "Account updated successfully"}


@router.delete("/accounts")
def delete_account(app_secret_token: str, db: Session = Depends(get_db)):
    if not app_secret_token:
        raise HTTPException(status_code=404, detail="Token Doesn't exist.")
    # Decode the JWT token to get the account_id
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token.get('account_id')
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Delete associated destinations
    destinations =  db.query(Destination).filter(Destination.account_id == account_id).all()
    for destination in destinations:
        db.delete(destination)

    db.delete(account)
    db.commit()
    return {"message": "Account and associated destinations deleted successfully"}

@router.post("/accounts/destinations")
def create_destination(app_secret_token: str, destination: Destination_check, db: Session = Depends(get_db)):
    if not app_secret_token:
        raise HTTPException(status_code=404, detail="Token Doesn't exist.")
    # Decode the JWT token to get the account_id
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token.get('account_id')
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db_account = db.query(Destination).filter(and_(Destination.url==destination.url,Destination.http_method==destination.http_method ,Destination.headers==destination.headers, Destination.account_id==account_id)).first()
    if db_account:
        raise HTTPException(status_code=404, detail="Destination already exist.")
    new_destinations = Destination(url=destination.url, http_method=destination.http_method , headers=destination.headers, account_id=account_id)
    db.add(new_destinations)  # Add the new_account instance to the session
    db.commit()
    db.refresh(new_destinations)
    db.commit()
    return {"message": "Destination created successfully"}

@router.get("/accounts/destinations")
def get_destinations(app_secret_token: str, db: Session = Depends(get_db)):
    if not app_secret_token:
        raise HTTPException(status_code=404, detail="Token Doesn't exist.")
    # Decode the JWT token to get the account_id
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token.get('account_id')
    destination = db.query(Destination).filter(Destination.account_id == account_id).all()
    if not destination:
        raise HTTPException(status_code=404, detail="Account not found")
    if not destination:
        return {"message": "No destinations found for the account"}
    return destination

@router.get("/acounts/access_token")
def get_access_token(data: dict, db: Session = Depends(get_db)):
    if 'email' not in data or 'account_id' not in data:
        raise HTTPException(status_code=402, detail="EmailID or AccountID Doesn't exist in body.")
    db_account = db.query(Account).filter(or_(Account.email == data.email, Account.account_id == data.account_id)).first()
    return {
        "message": "Account token successfully get.",
        "api_token": db_account.app_secret_token
    }
    
@router.delete("/accounts/destinations")
def delete_destinations(app_secret_token: str, db: Session = Depends(get_db)):
    if not app_secret_token:
        raise HTTPException(status_code=402, detail="Token Doesn't exist.")
    # Decode the JWT token to get the account_id
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token.get('account_id')
    account = db.query(Destination).filter(Destination.account_id == account_id).all()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    destinations =  db.query(Destination).filter(Destination.account_id == account_id).all()
    for destination in destinations:
        db.delete(destination)
    
    db.commit()

    return {"message": "Destinations deleted successfully"}

@router.post("/server/incoming_data")
def receive_data(data: dict, db: Session = Depends(get_db)):
    if not data:
        raise HTTPException(status_code=400, detail="Invalid Data")
    app_secret_token = data.get('app_secret_token', '')
    if not app_secret_token:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    token = jwt.decode(app_secret_token, "secret", algorithms=["HS256"])
    account_id = token.get('account_id')
    # Find the account based on the app secret token
    account = db.query(Account).filter(Account.account_id == account_id).first()
    # account = db.query(Account).filter(Account.app_secret_token == app_secret_token).first()
    if not account:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    
    # Send data to destinations
    for destination in account.destinations:
        headers = destination.headers.copy()
        headers["CL-XTOKEN"] = app_secret_token
        
        if destination.http_method == "GET":
            response = requests.get(destination.url, params=data, headers=headers)
        elif destination.http_method == "POST":
            response = requests.post(destination.url, json=data, headers=headers)
        elif destination.http_method == "PUT":
            response = requests.put(destination.url, json=data, headers=headers)
        else:
            raise HTTPException(status_code=400, detail="Invalid HTTP method")
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send data to destination")
    
    return {"message": "Data sent to destinations successfully"}
