# main.py

import uvicorn

from database import Base, engine
from views import router

# Create tables in the database
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    uvicorn.run(router, host="127.0.0.1", port=8000)
