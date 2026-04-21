import os
import io
import asyncio
from flask import (
    Flask,
    redirect,
    render_template,
    Response,
    url_for,
    send_file,
    jsonify,
    request,
)
from mcfetch import Player

from .config import Config
from core import fetch_player_web
from core.api import SKINS_API
from core.stats import StatsRenderer
from core import mojang_session


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)

app = Flask(__name__)
app.config.from_object(Config)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/invite")
def invite():
    return redirect(
        "https://discord.com/oauth2/authorize?client_id=1299030554641039371"
    )


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


async def handle_player(ign):
    result = await fetch_player_web(ign)
    if not result:
        return None

    uuid, player_obj = result
    ign = Player(player=uuid, requests_obj=mojang_session).name
    skin_bytes = await SKINS_API.fetch_skin_model(uuid)

    renderer = StatsRenderer(
        skin_model_bytes=skin_bytes,
        username=ign,
        player_uuid=uuid,
        player=player_obj,
        mode="Overall",
        view="Overall",
    )

    return await renderer.render()

@app.route("/api/player")
def api_player():
    ign = request.args.get("ign")

    if not ign:
        return jsonify({"error": "Missing IGN"}), 400

    try:
        image_bytes = loop.run_until_complete(handle_player(ign))

        if not image_bytes:
            return jsonify({"error": "Invalid player or never played"}), 404

        return send_file(io.BytesIO(image_bytes), mimetype="image/png")

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run()
