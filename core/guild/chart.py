import io
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from core.api.helpers import GuildInfo


async def generate_xp_chart(
    x: list,
    y: list,
    colors: list,
    guild_id: int,
    current_week: int,
    high_quality: bool = False,
) -> bytes:
    if not x or not y:
        return b""

    data = sorted(zip(x, y, colors), key=lambda item: item[1], reverse=True)
    x, y, colors = map(list, zip(*data))

    if colors:
        colors[0] = "#2ecc71"
        for i in range(1, min(5, len(colors))):
            colors[i] = "#1f8b4c"

    plt.style.use(
        "https://github.com/dhaitz/matplotlib-stylesheets/raw/master/pitayasmoothie-dark.mplstyle"
    )

    dpi = 300 if high_quality else 100
    plt.figure(figsize=(16, 6), dpi=dpi)

    plt.margins(x=0.01)

    bars = plt.bar(
        x,
        y,
        color=colors,
        edgecolor="black",
        linewidth=1.5,
    )

    plt.bar_label(
        bars,
        fontsize=13,
        rotation=90,
        padding=10,
        fmt="%.1f",
    )

    max_y = max(y) if y else 0
    plt.ylim(0, max(1, max_y * 1.15))

    plt.xticks(fontsize=14, rotation=90)

    legend_items = [
        mpatches.Patch(facecolor="#2ecc71", edgecolor="white", label="#1 Stars", linewidth=2),
        mpatches.Patch(facecolor="#1f8b4c", edgecolor="white", label="Top 5 stars", linewidth=2),
        mpatches.Patch(facecolor="#1685F8", edgecolor="white", label=">= 2 stars"),
        mpatches.Patch(facecolor="#F32C55", edgecolor="white", label="< 2 Stars"),
    ]

    plt.legend(handles=legend_items, loc="upper right", fontsize=16)

    guild_data = await GuildInfo.fetch(guild_id)

    year = current_week // 100
    week = current_week % 100

    plt.figtext(
        0.5,
        0.94,
        f"{guild_data.name} XP Chart",
        fontsize=25,
        ha="center",
        fontweight="bold",
    )

    plt.figtext(
        0.5,
        0.885,
        f"Week {week}, {year}",
        fontsize=16,
        ha="center",
    )

    plt.figtext(
        0.85,
        0.885,
        f"Total Stars: {round(sum(y))}",
        fontsize=16,
        ha="center",
    )

    buffer = io.BytesIO()
    plt.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
        pad_inches=0.25,
        dpi=dpi,
    )

    plt.close()
    buffer.seek(0)

    return buffer.getvalue()


async def generate_gxp_chart(
    x: list,
    y: list, 
    current_week: int,
    high_quality=False
) -> bytes:
    if not x or not y:
        return b""

    data = sorted(zip(x, y), key=lambda i: i[1], reverse=True)
    x, y = map(list, zip(*data))

    hex_colours = [
        "#663399",
        "#8262BB",
        "#9E90DD",
        "#BABFFF",
        "#6E73BC",
        "#222779",
        "#392B84",
        "#4F2F8E"
    ]
    colours = [hex_colours[i % len(hex_colours)] for i in range(len(x))]

    plt.style.use("https://github.com/dhaitz/matplotlib-stylesheets/raw/master/pitayasmoothie-dark.mplstyle")

    dpi = 300 if high_quality else 100
    plt.figure(figsize=(16, 6), dpi=dpi)
    plt.margins(x=0.01)

    bars = plt.bar(x, y, edgecolor="black", linewidth=1.8, color=colours)

    formatted_labels = [f"{int(v):,}" for v in y]
    plt.bar_label(bars, formatted_labels, fontsize=12, padding=4)

    year = current_week // 100
    week = current_week % 100

    plt.figtext(0.5, 0.95, "GXP Chart", fontsize=25, ha="center", fontweight="bold")
    plt.figtext(0.5, 0.9, f"Week {week}, {year}", fontsize=16, ha="center")
    plt.figtext(0.85, 0.9, f"Total GXP: {sum(y):,}", fontsize=16, ha="center")

    plt.xticks(fontsize=14, rotation=90)

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0.25, dpi=dpi)
    plt.close()
    buffer.seek(0)

    return buffer.getvalue()