import os, uuid
from pathlib import Path
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)
UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)

API_KEY = os.getenv("BIGJPG_API_KEY", "")
API = "https://bigjpg.com/api/task/"

def find_value(obj, wanted):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if k.lower() in wanted:
                return v
            x=find_value(v,wanted)
            if x is not None:
                return x
    elif isinstance(obj,list):
        for v in obj:
            x=find_value(v,wanted)
            if x is not None:
                return x
    return None

def find_url(obj):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if isinstance(v,str) and v.startswith(("http://","https://")):
                if any(w in k.lower() for w in ["url","result","output","download","image"]):
                    return v
            x=find_url(v)
            if x: return x
    elif isinstance(obj,list):
        for v in obj:
            x=find_url(v)
            if x: return x
    return None

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/api/upscale")
def create_task():
    if not API_KEY:
        return jsonify(error="Server API key is not configured."), 500

    f=request.files.get("image")
    if not f or not f.filename:
        return jsonify(error="Please choose an image."),400

    ext=Path(f.filename).suffix.lower()
    if ext not in [".jpg",".jpeg",".png",".webp"]:
        return jsonify(error="Use JPG, PNG or WEBP."),400

    filename=f"{uuid.uuid4().hex}{ext}"
    f.save(UPLOADS/filename)

    image_url=request.host_url.rstrip("/") + "/uploads/" + filename

    # BigJPG: x2=2 means 4x. Photo mode + high noise reduction.
    payload={
        "style":"photo",
        "noise":"2",
        "x2":"2",
        "file_name":f.filename,
        "input":image_url
    }

    try:
        r=requests.post(API,headers={"X-API-KEY":API_KEY},json=payload,timeout=60)
        r.raise_for_status()
        data=r.json()
    except Exception as e:
        return jsonify(error="BigJPG request failed.", detail=str(e)),502

    tid=find_value(data,{"tid","task_id","taskid"})
    if tid is None:
        tid=find_value(data,{"id"})
    if tid is None:
        return jsonify(error="BigJPG did not return a task ID.",response=data),502

    return jsonify(task_id=str(tid))

@app.get("/api/status/<task_id>")
def status(task_id):
    try:
        r=requests.get(API+task_id,timeout=30)
        r.raise_for_status()
        data=r.json()
    except Exception as e:
        return jsonify(error="Could not query BigJPG.",detail=str(e)),502

    result=find_url(data)
    status=find_value(data,{"status","state","stage"})
    status=(str(status).lower() if status is not None else "")

    if result:
        return jsonify(status="done",url=result)

    if status in {"failed","failure","error","cancelled","canceled"}:
        return jsonify(status="failed")

    return jsonify(status="processing")

@app.get("/uploads/<path:name>")
def uploaded(name):
    return send_from_directory(UPLOADS,name)

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
