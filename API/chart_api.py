from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
import os

app = FastAPI()

# 图片文件夹路径
img_dir = "/root/chart/"

@app.get("/{image_name}")
async def get_image(image_name: str):
    # 构造图片文件的完整路径
    image_path = os.path.join(img_dir, image_name)
    # 检查文件是否存在
    if os.path.exists(image_path):
        return FileResponse(image_path)
    else:
        return {"error": "Image not found"}


if __name__ == "__main__":
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=6300)
