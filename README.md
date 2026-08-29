# BigJPG 4x Website

Upload an image and the website automatically sends it to BigJPG with:
- style: photo
- noise: 2 (High)
- x2: 2 (4x)

## Deploy
Use Render, Railway, or another Python web host that gives the app a public HTTPS URL.

Set the environment variable:
BIGJPG_API_KEY=YOUR_BIGJPG_KEY

Never put the API key in HTML or JavaScript.

BigJPG's API requires an image URL, so the server hosts the uploaded image at `/uploads/...` and sends that public URL to BigJPG. The site then polls the task endpoint until a result URL is returned.

If you use Render:
Build: pip install -r requirements.txt
Start: gunicorn app:app
