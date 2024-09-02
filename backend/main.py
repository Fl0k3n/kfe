import base64
import io

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,  # Allow cookies to be sent with the requests
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


# paginated file endpoints, should deliver files (with thumnails) in some range, ordered by some metric
@app.get("/files")
async def get_files():
    return [
        {
            "name": "some file",
            "metadata": "TODO"
        }
    ]


# here we accept a search query and return K files
@app.post("/search")
async def search():
    return await get_files()


# here we accept a file and return a list of similar files
@app.post("/similarity")
async def find_similar_files():
    return await get_files()



@app.get("/files-testing")
async def load_sample_files():
    target_dir = '/home/flok3n/minikonrad'

    sample_images = [
        'Screenshot from 2024-06-01 12-27-54.png',
        '352943037_810199457382291_7070402249034345132_n.jpg'
    ]

    res = []
    for filename in sample_images:
        buff = io.BytesIO()
        img = Image.open(f'{target_dir}/{filename}').convert('RGB')
        img.thumbnail((400, 400))
        img.save(buff, format="JPEG")
        base64_thumbnail = base64.b64encode(buff.getvalue()).decode()
        res.append({
            "name": filename,
            "thumbnail": base64_thumbnail
        })
    return res

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
