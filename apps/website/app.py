import os
from flask import Flask, redirect, render_template, Response, url_for
from config import Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)

app = Flask(__name__)
app.config.from_object(Config)


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/invite")
def invite():
    return redirect("https://discord.com/oauth2/authorize?client_id=1299030554641039371")


@app.route("/discord")
def discord():
    return redirect("https://discord.gg/ZEjc4G2bDx")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.route("/sitemap.xml")
def sitemap():
    pages = []

    pages.append(url_for("index", _external=True))
    pages.append(url_for("invite", _external=True))
    pages.append(url_for("discord", _external=True))

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append(
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    )

    for page in pages:
        sitemap_xml.append(f"""
        <url>
            <loc>{page}</loc>
        </url>
        """)

    sitemap_xml.append("</urlset>")

    return Response("\n".join(sitemap_xml), mimetype="application/xml")


if __name__ == "__main__":
    app.run()