from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError
import requests

app = FastAPI()

# Account Model
class Account(BaseModel):
    email: str
    account_id: str
    account_name: str
    app_secret_token: str
    website: str = None

# Destination Model
class Destination(BaseModel):
    url: str
    http_method: str
    headers: dict[str, str]

# In-memory storage for accounts and destinations
accounts = {}
destinations = {}

# API to create an account
@app.post("/accounts")
def create_account(account: Account):
    try:
        if account.email in accounts:
            raise HTTPException(status_code=400, detail="Account already exists")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) 
    accounts[account.account_id] = account
    return {"message": "Account created successfully"}

# API to get an account by account id
@app.get("/accounts/{account_id}")
def get_account(account_id: str):
    if account_id in accounts:
            return accounts[account_id]
    raise HTTPException(status_code=404, detail="Account not found")

# API to update an account
@app.put("/accounts/{account_id}")
def update_account(account_id: str, account: Account):
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    accounts[account_id] = account
    return {"message": "Account updated successfully"}

# API to delete an account
@app.delete("/accounts/{account_id}")
def delete_account(account_id: str):
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    del accounts[account_id]
    # Delete destinations associated with the account
    destinations.pop(account_id, None)
    return {"message": "Account deleted successfully"}

# API to create a destination for an account
@app.post("/accounts/{account_id}/destinations")
def create_destination(account_id: str, destination: Destination):
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    if account_id not in destinations:
        destinations[account_id] = []
    print(Destination)
    for des in destinations[account_id]:
        if destination==des:
            return HTTPException(status_code=202, detail="Destination already exist", headers=destination.headers)
    destinations[account_id].append(destination)
    return {"message": "Destination created successfully"}

# API to get destinations for an account
@app.get("/accounts/{account_id}/destinations")
def get_destinations(account_id: str):
    if account_id not in accounts:
        raise HTTPException(status_code=404, detail="Account not found")
    if account_id not in destinations or len(destinations[account_id]) == 0:
        return {"message": "No destinations found for the account"}
    return destinations[account_id]

# API to Delete destinations for an account
@app.delete("/accounts/{account_id}/destinations")
def delete_account(account_id: str):
    if account_id not in destinations:
        raise HTTPException(status_code=404, detail="Account not found")
    # Delete destinations associated with the account
    destinations.pop(account_id, None)
    return {"message": "Account deleted successfully"}


# API to receive data and send it to destinations
@app.post("/server/incoming_data")
def receive_data(data: dict, app_secret_token: str):
    if not data:
        raise HTTPException(status_code=400, detail="Invalid Data")
    if not app_secret_token:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    
    # Find the account based on the app secret token
    account = None
    print(accounts)
    for acc in accounts.values():
        if acc.app_secret_token == app_secret_token:
            account = acc
            break
    if not account:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    
    # Send data to destinations
    for destination in destinations.get(account.account_id, []):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)