import uvicorn
from dotenv import load_dotenv

# Load environment variables at the start
load_dotenv()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=5001, reload=True)
