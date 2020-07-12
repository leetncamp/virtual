import argparse
import json

import requests
from ics.icalendar import Calendar


# import ics


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="MiniConf Calendar Command Line")

    parser.add_argument(
        "ics",
        default="sample_cal.ics",
        type=str,
        help="ICS file to parse (local or via http)",
    )

    parser.add_argument(
        "--out", default="../static/virtual/data/icml_calendar.json",
        help="ICS file to parse"
    )

    return parser.parse_args()


# pylint: disable=redefined-outer-name
def convert(args):
    file_ics: str = args.ics
    if not file_ics.startswith("http"):
        with open(file_ics, "r") as f:
            c = Calendar(f.read())
    else:
        c = Calendar(requests.get(file_ics).text)

    collector = []
    for e in c.events:
        title = e.name
        tpe = "---"

        # check for starting hashtag
        parts = title.split(" ")
        if parts[0].startswith("#"):
            tpe = parts[0][1:]
            title = " ".join(parts[1:])

        # print(e.description)
        # print(e.url)

        if title.startswith('EXPO'):
            tpe = 'expo'
        elif title.startswith('Poster'):
            tpe = 'poster'
        elif title.startswith('Tutorial'):
            tpe = 'tutorial'
        elif title.startswith('Invited'):
            tpe = 'invited'
        elif title.endswith('orkshop') or 'ueer' in title or 'atinX' in title:
            tpe = 'workshop'


        link = e.url
        if not link:
            link = e.description

        # // const
        # toreturn = {
        #            // title,
        # // "location": "",
        # // id: '' + id,
        # // calendarId: title.startsWith("Poster") ? '1': '2', // + (id % 2 + 1),
        # // category: 'time',
        # // dueDateClass: ''
        #                  //
        #                  //};

        json_event = {
            "title": title,
            "start": e.begin.for_json(),
            "end": e.end.for_json(),
            "location": e.location,
            "link": link,
            "category": "time",
            "calendarId": tpe,
        }
        collector.append(json_event)
        print(json_event)

    with (open(args.out, "w")) as f:
        json.dump(collector, f)

    # print(c.events)

    pass


if __name__ == "__main__":
    args = parse_arguments()
    convert(args)
