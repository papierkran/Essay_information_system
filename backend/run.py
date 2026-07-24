import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="::", port=6886, reload=True)
