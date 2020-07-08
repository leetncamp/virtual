from django.shortcuts import render
from pdb import set_trace as debug
import traceback
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse, FileResponse
from nips.conference import ConferenceInfo
from django.template.loader import get_template
from django.conf import settings
from django.urls import reverse
from datetime import datetime
import pickle
import json
import os
import io
from django.urls import reverse
from django.contrib import messages


from nips.models import Events, Eventspeakers, Timezones, Conferences, Registrations, Users, conferenceDict, Userlinks, now, Q, escape

import logging
log = logging.getLogger(__name__)


def get_access(request, year):
    """Does the request user have access to the virtual site? If registered or free then yes"""

    # is the conference already free?
    becomes_free_date = Conferences.objects.get(
        pk=settings.CURRENT_CONFERENCE).becomes_free_after

    if becomes_free_date:
        free = now() > becomes_free_date
    else:
        free = False

    if free:
        return(True)

    if request.user.is_authenticated:
        linked_users = request.user.get_all_user_links()
        paid_registrations = Registrations.objects.filter(
            conference__id=settings.CURRENT_CONFERENCE, user__in=linked_users).filter(Q(status="Paid") | Q(status="Refund Due"))
    else:
        paid_registrations = Registrations.objects.none()

    return(paid_registrations.exists())


def getConfInfo(request, year=None):
    confInfo = conferenceDict.get(
        (year, request.user.username),  ConferenceInfo(request, year))
    confInfo.refresh()
    conferenceDict.update({(confInfo.year, request.user.username): confInfo})
    return(confInfo)


def home(request, year):

    confInfo = getConfInfo(request, year=year)
    timezone_nextp = request.get_full_path()
    return(render(request, "virtual/index.html", locals()))


def papers(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    papers = Events.objects.filter(
        session__conference__id=year, type="Poster").order_by("?")

    search_type = request.GET.get("search_type")
    if search_type:
        search_query = request.GET.get("search")

        if search_query:
            if search_type == "author":
                # We might search by PK of author or by string

                try:
                    pk = int(search_query)
                    speakers = Users.objects.filter(pk=pk)
                except ValueError:

                    """We are searching for authors by string. Check first and last name and also check for linked users"""

                    queries = search_query.split()
                    query = queries.pop()
                    speakers = Users.objects.filter(
                        Q(firstname__icontains=query) | Q(lastname__icontains=query))

                    for query in queries:
                        qspeakers = Users.objects.filter(
                            Q(firstname__icontains=query) | Q(lastname__icontains=query))
                        speakers = speakers.intersection(qspeakers)

                linked_users = Userlinks.objects.none()
                for speaker in speakers:
                    linked_users = linked_users.union(
                        speaker.get_all_user_links())
                linked_users = linked_users.distinct()
                papers = Events.objects.filter(pk__in=Eventspeakers.objects.filter(speaker__id__in=list(
                    linked_users.values_list("pk", flat=True))).values("event")).distinct()
            elif search_type == "title":
                queries = search_query.split()
                query = queries.pop()
                papers = Events.objects.filter(name__icontains=query)
                for query in queries:
                    papers = papers.intersection(
                        Events.objects.filter(name__icontains=query))

            elif search_type == "keyword":
                queries = search_query.split()
                query = queries.pop()
                papers = Events.objects.filter(
                    subject_areas__name__icontains=query)
                for query in queries:
                    papers = papers.intersection(Events.objects.filter(
                        subject_areas__name__icontains=query))
    else:

        search_type = "keyword"
    papers = Events.objects.filter(pk__in=list(papers.distinct().values_list(
        "pk", flat=True)), session__conference__id=settings.CURRENT_CONFERENCE).order_by("?")

    all_papers = Events.objects.filter(session__conference__id=settings.CURRENT_CONFERENCE, type="Poster")
    keywords = all_papers.exclude(subject_areas=None).order_by("subject_areas__name").values_list("subject_areas__name", 
        flat=True).distinct().order_by("subject_areas__name")  #used in as source of Show topics/keywords »
    keyword_list = json.dumps([i for i in keywords]) #used in typeahead

    titles_list = json.dumps([i for i in all_papers.values_list("name", flat=True).distinct().order_by("name")])
    
    #Calculating names take almost 5 seconds becuase I don't cache the full name in the user model.  Calculate and store them in a pickle.

    author_list_path = "/tmp/author-list-{}.pickle".format(settings.DATABASE)

    if os.path.isfile(author_list_path):
        author_list = pickle.load(open(author_list_path, 'rb'))
    else:
        author_names = set()
        log.warning("Calculating author names for virtual paper page. This might take 10 seconds")
        for pap in all_papers:
            for speaker in pap.get_speakers():
                author_names.add(speaker.get_full_name())
        author_list = [i for i in author_names]

        outfile = open(author_list_path, 'wb')
        pickle.dump(author_list, outfile)
    author_list = json.dumps(author_list)

    return(render(request, "virtual/papers.html", locals()))


def ical(request, eventid, number):

    """number is either the first or 2nd instance of this presentation"""



    if request.user.is_authenticated:
        access_granted = True

        if access_granted:

            conf_event = Events.objects.filter(pk=eventid).first()

            from icalendar import Calendar, Event
            from nips.models import IcalUserEvents
            cal = Calendar()
            cal.add('prodid', '-//ICML 2020//icml.cc//')
            cal.add('version', '2.0')

            event = Event()
            event.add('summary', conf_event.name)
            if number == 1:
                event.add('dtstart', conf_event.starttime)
                event.add('dtend', conf_event.endtime)
            elif number == 2:
                event.add('dtstart', conf_event.starttime2)
                event.add('dtend', conf_event.endtime2)
            event.add('dtstamp', now())


            from icalendar import vCalAddress, vText
            domain = conf_event.session.conference.organization.get_domain()
            organizer = vCalAddress('MAILTO:do-not-reply@icml.cc')

            speakers = conf_event.get_speakers()
            if speakers:
                speaker = speakers[0]
                organizer.params['cn'] = vText(speaker.get_full_name())
            else:
                speaker = ''

            

            event['organizer'] = organizer



            if conf_event.type == "Poster":
                event['url'] = request.build_absolute_uri(reverse("virtual_paper_detail", args=[conf_event.session.conference.id, conf_event.id]))

            event['uid'] = '{}'.format(request.get_full_path())
            event['location'] = vText(conf_event.get_semicolonSpeakerStr())


            cal.add_component(event)
            
            tmp = io.BytesIO()
            tmp.write(cal.to_ical())
            tmp.flush()
            tmp.seek(0)
            response = HttpResponse(
                tmp.read(), content_type="application/octet-stream")
            response['Content-Disposition'] = 'attachment; filename="{0}.ics"'.format(
                event['uid'])

            icaluserevent, created = IcalUserEvents.objects.get_or_create(user=request.user, event=conf_event, number=number)
            if created:
                icaluserevent.save()
                log.info("ICALEVENT {}".format(icaluserevent))
        else:
            log.info("User {} acessed an ical link without having access")
            return HttpResponseNotFound('<h1>You are not logged in and registered</h1>')
    else:
        return HttpResponseNotFound('<h1>You are not logged in and registered</h1>')

    return(response)


def paper_vis(request, year):

    confInfo = getConfInfo(request, year=year)

    papers = Events.objects.filter(
        session__conference__id=year, type="Poster").order_by("?")

    return(render(request, "virtual/paper_vis.html", locals()))

def paper_detail(request, year, eventid):

    confInfo = getConfInfo(request, year=year)

    paper = Events.objects.filter(
        pk=eventid, session__conference__id=year).first()

    access_granted = get_access(request, year)

    """Create or get the rocketchat channel for this paper and make sure the request user has a rocketchat account"""
    from rocketchat_conferences import helpers as rch

    rci = rch.get_active_rocketchat_conf_inst_obj()

    if access_granted and paper and rci:

        rcu = rch.find_or_create_user(request.user)

        try:

            event_channel = rch.find_or_create_events_channel(paper)

            if event_channel:

                rocketchat_new_window_url = "{}?resumeToken={}".format(
                    event_channel.get_url(), rcu.rocketchat_token)

                rocketchat_iframe_url = "{}?layout=embedded".format(
                    event_channel.get_url(), rcu.rocketchat_token)

                rocketchat_iframe_id = 'eventPageChat'

                event_channel_auth_js = rch.make_authenticate_script_js(
                    rocketchat_iframe_id, rcu.rocketchat_token)

        except Exception as e:

            msg = str(e) + traceback.format_exc()

            log.critical(msg)

    return(render(request, "virtual/paper_detail.html", locals()))


def events(request, year, event_type):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    events = Events.objects.filter(
        session__conference__id=year, type__istartswith=event_type).order_by("?")

    search_type = request.GET.get("filter")
    if search_type:
        search_query = request.GET.get("search")
        if search_query:
            if search_type == "authors":
                speaker = Users.objects.filter(pk=search_query).first()
                if speaker:
                    linked_users = speaker.get_all_user_links()
                    events = Events.objects.filter(pk__in=Eventspeakers.objects.filter(
                        speaker__in=linked_users).values("event"))

    events = events.exclude(uniqueid__endswith="-2nd")

    return(render(request, "virtual/events.html", locals()))


def workshops(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    wks = Events.objects.filter(
        session__conference__id=year, type__istartswith="Workshop").order_by("?")

    return(render(request, "virtual/workshops.html", locals()))
