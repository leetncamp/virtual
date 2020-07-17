import argparse
import json
import os
import csv


def parse_arguments():
    parser = argparse.ArgumentParser(description="MiniConf Portal Command Line")

    parser.add_argument("workshops", help="papers file to parse")
    parser.add_argument("--out",
                        default="../static/virtual/data/icml_workshops.json",
                        help="out file")

    return parser.parse_args()


def add_file(file_name, all_socials, type):
    if os.path.exists(file_name):
        with open(file_name, encoding='utf-8-sig') as input_file:
            reader = csv.DictReader(input_file)
            for event in reader:
                print(event)
                poster_entry = {
                    "title": event["title"],
                    "id": event["id"],
                    "type": type,
                    "start": event['start']
                }

                all_socials.append(poster_entry)

        print("{} entries".format(len(all_socials)))

    else:
        print('file does not exist: ' + file_name)

    # Title, Description, Session1, Session1_zoom, Session2, Session2_zoom

    # {
    #     "id": v["UID"],
    #     "forum": v["UID"],
    #     "content": {
    #         "title": v["title"],
    #         "authors": list_fields["authors"],
    #         "keywords": list_fields["keywords"],
    #         "abstract": v["abstract"],
    #         "TLDR": v["abstract"],
    #         "recs": [],
    #         "session": list_fields["session"],
    #         "pdf_url": v.get("pdf_url", ""),
    #     },
    # }


if __name__ == "__main__":
    args = parse_arguments()
    all_events = []
    add_file(args.workshops, all_events, 'social')
    # add_file(args.mentoring, all_events, 'mentoring')
    # for event in all_events:
    #     if len(event['sessions']) > 1:
    #         print(event)

    with open(args.out, 'w') as out_file:
        json.dump(all_events, out_file)
    # print(all_events)
