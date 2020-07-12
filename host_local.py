# pylint: disable=global-statement,redefined-outer-name
import argparse
import csv
import glob
import json
import os

import yaml
from flask import Flask, jsonify, redirect, render_template, send_from_directory
from flask_frozen import Freezer
from flaskext.markdown import Markdown

site_data = {}
by_uid = {}
urls = {
    "paper_vis": "paper_vis.html",
    "papers": "papers.html",
    "main_style": "/static/virtual/css/virtual.css",
    "logo": "https://icml.cc/static/nips/img/ICML-logo.svg",
    "expo_img": "https://icml.cc/static/expo/img/icml/expo-logo-nav.png",
    "expo": "https://icml.cc/ExpoConferences/2020/Expo",
    "workshops": "workshops.html",
    "js": '/static/virtual/js',
    "css": '/static/virtual/css',
    "data_dir": '/static/virtual/data',
    "thumbnail_dir": "/static/virtual/img/paper_thumbnails/icml/2020"
}

confInfo = {
    "user": {
        "is_superuser": True
    },
    "conference": "ICML 2020"
}

request = {
    "user": {
        "is_authenticated": True,
        "is_superuser": True
    }
}

pagePermission = {
    'change': False
}




def main(site_data_path):
    global site_data, extra_files
    extra_files = []
    # Load all for your sitedata one time.
    for f in glob.glob(site_data_path + "/*"):
        extra_files.append(f)
        name, typ = f.split("/")[-1].split(".")
        if typ == "json":
            site_data[name] = json.load(open(f))
        elif typ in {"csv", "tsv"}:
            site_data[name] = list(csv.DictReader(open(f)))
        elif typ == "yml":
            site_data[name] = yaml.load(open(f).read(), Loader=yaml.SafeLoader)

    for typ in ["papers", "speakers", "workshops"]:
        by_uid[typ] = {}
        for p in site_data[typ]:
            by_uid[typ][p["UID"]] = p

    print("Data Successfully Loaded")
    return extra_files


# ------------- SERVER CODE -------------------->

app = Flask(__name__, template_folder='templates/virtual')
app.config.from_object(__name__)
freezer = Freezer(app)
markdown = Markdown(app)


# MAIN PAGES


def _data():
    data = {}
    data["config"] = site_data["config"]
    data["urls"] = urls
    data["confInfo"] = confInfo
    data["request"] = request
    data["pagePermission"] = pagePermission
    data["access_granted"] = True
    data["tz_offset"] = '-240'
    data["tz_name"] = 'America/New York'
    return data


@app.route("/")
def index():
    return redirect("/index.html")


# TOP LEVEL PAGES


# @app.route("/index.html")
# def home():
#     data = _data()
#     data["readme"] = ''  # open("README.md").read()
#     data["committee"] = site_data["committee"]["committee"]
#     return render_template("index.html", **data)


# @app.route("/about.html")
# def about():
#     data = _data()
#     data["FAQ"] = site_data["faq"]["FAQ"]
#     return render_template("about.html", **data)


@app.route("/papers.html")
def papers():
    data = _data()
    data["papers"] = site_data["papers"]
    return render_template("papers.html", **data)


@app.route("/paper_vis.html")
def paper_vis():
    data = _data()
    return render_template("paper_vis.html", **data)

@app.route("/socials.html")
def socials():
    data = _data()
    return render_template("socials.html", **data)

@app.route("/calendar.html")
def cal():
    data = _data()
    return render_template("calendar.html", **data)

# @app.route("/calendar.html")
# def schedule():
#     data = _data()
#     data["day"] = {
#         "speakers": site_data["speakers"],
#         "highlighted": [
#             format_paper(by_uid["papers"][h["UID"]]) for h in site_data["highlighted"]
#         ],
#     }
#     return render_template("virtual/schedule.html", **data)


# @app.route("/workshops.html")
# def workshops():
#     data = _data()
#     data["workshops"] = [
#         format_workshop(workshop) for workshop in site_data["workshops"]
#     ]
#     return render_template("workshops.html", **data)


def extract_list_field(v, key):
    value = v.get(key, "")
    if isinstance(value, list):
        return value
    else:
        return value.split("|")


def format_paper(v):
    list_keys = ["authors", "keywords", "session"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["UID"],
        "forum": v["UID"],
        "content": {
            "title": v["title"],
            "authors": list_fields["authors"],
            "keywords": list_fields["keywords"],
            "abstract": v["abstract"],
            "TLDR": v["abstract"],
            "recs": [],
            "session": list_fields["session"],
            "pdf_url": v.get("pdf_url", ""),
        },
    }


def format_workshop(v):
    list_keys = ["authors"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["UID"],
        "title": v["title"],
        "organizers": list_fields["authors"],
        "abstract": v["abstract"],
    }


# ITEM PAGES


# @app.route("/poster_<poster>.html")
# def poster(poster):
#     uid = poster
#     v = by_uid["papers"][uid]
#     data = _data()
#     data["paper"] = format_paper(v)
#     return render_template("poster.html", **data)
#
#
# @app.route("/speaker_<speaker>.html")
# def speaker(speaker):
#     uid = speaker
#     v = by_uid["speakers"][uid]
#     data = _data()
#     data["speaker"] = v
#     return render_template("speaker.html", **data)
#
#
# @app.route("/workshop_<workshop>.html")
# def workshop(workshop):
#     uid = workshop
#     v = by_uid["workshops"][uid]
#     data = _data()
#     data["workshop"] = format_workshop(v)
#     return render_template("workshop.html", **data)
#
#
# @app.route("/chat.html")
# def chat():
#     data = _data()
#     return render_template("chat.html", **data)


# FRONT END SERVING


# @app.route("/papers.json")
# def paper_json():
#     json = []
#     for v in site_data["papers"]:
#         json.append(format_paper(v))
#     return jsonify(json)


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


# @app.route("/serve_<path>.json")
# def serve(path):
#     return jsonify(site_data[path])


# --------------- DRIVER CODE -------------------------->
# Code to turn it all static


# @freezer.register_generator
# def generator():
#
#     for paper in site_data["papers"]:
#         yield "poster", {"poster": str(paper["UID"])}
#     for speaker in site_data["speakers"]:
#         yield "speaker", {"speaker": str(speaker["UID"])}
#     for workshop in site_data["workshops"]:
#         yield "workshop", {"workshop": str(workshop["UID"])}
#
#     for key in site_data:
#         yield "serve", {"path": key}


def parse_arguments():
    parser = argparse.ArgumentParser(description="MiniConf Portal Command Line")

    parser.add_argument(
        "--build",
        action="store_true",
        default=False,
        help="Convert the site to static assets",
    )

    parser.add_argument(
        "-b",
        action="store_true",
        default=False,
        dest="build",
        help="Convert the site to static assets",
    )

    parser.add_argument("path",
                        help="Pass the JSON data path and run the server")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()

    site_data_path = args.path
    extra_files = main(site_data_path)

    if args.build:
        freezer.freeze()
    else:
        debug_val = True
        if os.getenv("FLASK_DEBUG") == "True":
            debug_val = True

        app.run(port=5000, debug=debug_val, extra_files=extra_files)