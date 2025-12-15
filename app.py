from flask import Flask, request, render_template_string
from auto_brain_core import process_video
from comment_finder import DEFAULT_KEYWORDS

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>TikTok Auto Likes</title>
<style>
body{background:#020617;color:#e5e7eb;font-family:system-ui}
.box{max-width:1000px;margin:40px auto;background:#0f172a;padding:20px;border-radius:16px}
textarea{width:100%;min-height:180px;background:#020617;color:#e5e7eb;padding:10px}
button{margin-top:10px;padding:10px 18px;border-radius:999px;border:none;background:#6366f1;color:white;font-weight:700}
pre{margin-top:15px;background:#020617;padding:10px;border-radius:10px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
</style>
</head>
<body>
<div class="box">
<h2>TikTok Auto Likes – Money Forbidden Compass</h2>
<form method="post">
<div class="grid">
<div>
<label>Video links (1 po liniji)</label>
<textarea name="links">{{links}}</textarea>
</div>
<div>
<label>Keywords (1 po liniji)</label>
<textarea name="keywords">{{keywords}}</textarea>
</div>
</div>
<button type="submit">🚀 Send Auto Likes</button>
</form>
{% if log %}<pre>{{log}}</pre>{% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    links = ""
    keywords = "\n".join(DEFAULT_KEYWORDS)
    logs = []

    if request.method == "POST":
        links = request.form.get("links", "")
        keywords = request.form.get("keywords", keywords)

        kw_list = [k.strip() for k in keywords.splitlines() if k.strip()]
        urls = [u.strip() for u in links.splitlines() if u.strip()]

        for url in urls:
            res = process_video(url, kw_list)
            logs.append(f"{url} -> {res}")

    return render_template_string(
        HTML,
        links=links,
        keywords=keywords,
        log="\n".join(logs)
    )

if __name__ == "__main__":
    app.run(debug=True)
