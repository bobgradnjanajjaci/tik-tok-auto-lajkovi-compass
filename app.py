from flask import Flask, request, render_template_string
from auto_brain_core import process_video

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Auto Likes – Money Forbidden Compass</title>
<style>
body{background:#020617;color:#e5e7eb;font-family:system-ui}
.box{max-width:900px;margin:40px auto;background:#0f172a;padding:20px;border-radius:16px}
textarea{width:100%;min-height:180px;background:#020617;color:#e5e7eb;padding:10px}
button{margin-top:10px;padding:10px 18px;border-radius:999px;border:none;background:#6366f1;color:white;font-weight:700}
pre{margin-top:15px;background:#020617;padding:10px;border-radius:10px}
</style>
</head>
<body>
<div class="box">
<h2>Money Forbidden Compass – Auto Likes</h2>
<form method="post">
<textarea name="links" placeholder="TikTok links (1 per line)">{{links}}</textarea>
<button type="submit">🚀 Run</button>
</form>
{% if log %}<pre>{{log}}</pre>{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    links = ""
    logs = []

    if request.method == "POST":
        links = request.form.get("links", "")
        for url in [u.strip() for u in links.splitlines() if u.strip()]:
            logs.append(f"{url} -> {process_video(url)}")

    return render_template_string(HTML, links=links, log="\n".join(logs))

if __name__ == "__main__":
    app.run()
