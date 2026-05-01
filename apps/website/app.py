import os
from quart import Quart, render_template, redirect, Response, url_for
from dotenv import load_dotenv

load_dotenv()

app = Quart(__name__)
app.secret_key = os.environ.get("SECRET_KEY")


@app.route("/")
async def index():
    return await render_template("index.html")


@app.route("/invite")
async def invite():
    return redirect("https://discord.com/oauth2/authorize?client_id=1299030554641039371")


@app.route("/discord")
async def discord():
    return redirect("https://discord.gg/ZEjc4G2bDx")


@app.route("/coming-soon")
async def coming_soon():
    return await render_template("coming-soon.html")


@app.errorhandler(404)
async def page_not_found(e):
    return await render_template("404.html"), 404


@app.errorhandler(500)
async def page_not_found(e):
    return await render_template("500.html"), 500


@app.route("/sitemap.xml")
async def sitemap():
    pages = []

    pages.append(url_for("index", _external=True))
    pages.append(url_for("invite", _external=True))
    pages.append(url_for("discord", _external=True))

    sitemap_xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap_xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for page in pages:
        sitemap_xml.append(
            f"""
        <url>
            <loc>{page}</loc>
        </url>
        """
        )

    sitemap_xml.append("</urlset>")

    return Response("\n".join(sitemap_xml), mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)