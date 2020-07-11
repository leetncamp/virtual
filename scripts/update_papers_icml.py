import argparse
import json
import os


def parse_arguments():
    parser = argparse.ArgumentParser(description="MiniConf Portal Command Line")

    parser.add_argument("papers", help="papers file to parse")
    parser.add_argument("--out", default="../static/data/icml_papers.json",
                        help="out file")

    return parser.parse_args()


def transform(papers, out):
    all_posters = []

    if os.path.exists(papers):
        all_events = []
        with open(papers) as papers_file:
            all_events = json.load(papers_file)
        for event in all_events:
            if event["type"] == "Poster":
                poster_entry = {
                    "id": event["sourceid"],
                    "forum": event["sourceid"],
                    "content": {
                        "title": event["title"],
                        "authors": list(
                            map(lambda a: "{} {} {}".format(a['firstname'], '',
                                                            # a['middleinitial'],
                                                            a['lastname']),
                                event["authors"])),
                        "keywords": event["subject_areas"],
                        "abstract": event["abstract"],
                        "TLDR": event["abstract"],
                        "recs": [],
                        "session": [],
                        "pdf_url": '',
                    },
                }
                all_posters.append(poster_entry)

        print("{} entries".format(len(all_posters)))

        with open(out, 'w') as out_file:
            json.dump(all_posters, out_file)

    else:
        print('file does not exist: ' + papers)

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
    transform(args.papers, args.out)
