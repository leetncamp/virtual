from django.shortcuts import render
from pdb import set_trace as debug
import traceback
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse, FileResponse, Http404
from nips.conference import ConferenceInfo
from django.template.loader import get_template
from django.conf import settings
from django.urls import reverse
from datetime import datetime, timedelta
import pickle
import json
import os
import io
from django.urls import reverse
from django.contrib import messages
import pytz
import time


from nips.models import Events, Eventspeakers, Timezones, Conferences, Registrations, Users, \
    conferenceDict, Userlinks, now, Q, escape, Sessions, Eventmedia
from nips.views import  SlideUploadForm

from django.utils.timezone import activate, deactivate, get_current_timezone

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
    pagePermission = confInfo.get_permission(textid=request.META.get("PATH_INFO", None))
    pagePermission['view'] = True
    timezone_nextp = request.get_full_path()
    return(render(request, "virtual/index.html", locals()))


def get_urls():
    
    urls = {
        "paper_vis": "paper_vis.html",
        "papers": "papers.html",
        "main_style": "/static/virtual/css/virtual.css",
        "logo": "https://icml.cc/static/nips/img/ICML-logo.svg",
        "expo_img": "https://icml.cc/static/expo/img/icml/expo-logo-nav.png",
        "expo": "https://icml.cc/ExpoConferences/2020/Expo",
        "workshops": "/virtual/2020/workshops",
        "js": '/static/virtual/js',
        "css": '/static/virtual/css',
        "data_dir": '/static/virtual/data',
        "thumbnail_dir": "/static/virtual/img/paper_thumbnails/icml/2020"
    }

    return urls

def get_timezone():  

    tz = get_current_timezone()
    tz_name = tz.zone
    local_now = datetime.now(tz)
    tz_offset = local_now.utcoffset().total_seconds() /60

    return(tz_name, tz_offset)


def papers(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)


    urls = get_urls()

    tz_name, tz_offset = get_timezone()

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
    
    #Calculating names take almost 5 seconds because I don't cache the full name in the user model.  Calculate and store them in a pickle.

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
                if conf_event.starttime and conf_event.endtime:
                    event.add('dtstart', conf_event.starttime)
                    event.add('dtend', conf_event.endtime)
                elif conf_event.starttime:  #Workshop organizers sometimes don't fill in the endtime
                    event.add('dtstart', conf_event.starttime)

                    event.add('dtstart', conf_event.starttime + timedelta(minutes=30))
                else:
                    raise Http404("An ical attachment cannot be generated.  An engineer has been notified. ")
            elif number == 2:
                if conf_event.starttime2 and conf_event.endtime2:
                    event.add('dtstart', conf_event.starttime2)
                    event.add('dtend', conf_event.endtime2)
                elif conf_event.starttime2:
                    event.add('dtstart', conf_event.starttime2)
                    event.add('dtstart', conf_event.starttime2 + timedelta(minutes=30))
                else:
                    raise Http404("An ical attachment cannot be generated.  An engineer has been notified. ")
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

    urls = get_urls()

    access_granted = get_access(request, year)

    tz_name, tz_offset = get_timezone()

    return(render(request, "virtual/paper_vis.html", locals()))



def process_slide_upload(request, event):
    max_size = 100 #MB

    try:
        pk = request.POST.get("presenter")

        slideUploadForm = SlideUploadForm(request.POST, request.FILES, event=event)

        if slideUploadForm.is_valid():
            try:
                presenter = Eventspeakers.objects.get(pk=pk)
                presenter.presenting = True
                presenter.save()
                if presenter.event.type in ['Spotlight', 'Oral']:
                    #For an oral or spotlight, there can only be one presenter
                    other_speakers = Eventspeakers.objects.filter(event=presenter.event).exclude(pk=presenter.pk)
                    other_speakers.update(presenting=False)
            except ValueError:
                pass
            pdf_file = slideUploadForm.cleaned_data.get("pdf_file")

            if len(pdf_file) > max_size * 1000000:
                messages.error(request, "File size is too large. Must be less than {0} MB.".format(max_size))
            elif not os.path.splitext(pdf_file.name)[1].lower() == ".pdf":
                messages.error(request, "File type must be PDF")
            else:
                if not event.location:
                    event.location = "Virtual" #A location is required in order to name the slide

                media_path = event.get_slide_path()
                media_dir = os.path.dirname(media_path)
                os.makedirs(media_dir, exist_ok=True)
                if len(pdf_file) > 0:
                    open(media_path, 'wb').write(pdf_file.read())
                    messages.success(request, "Success.  You should see a publicly visible link to your slides below.")
                    create_eventmedia = slideUploadForm.cleaned_data.get("downloadable", True)
                    create_eventmedia = True
                    if create_eventmedia:
                        em = Eventmedia.objects.filter(event=event, name="Slides", type="PDF").first()
                        if not em:
                            em = Eventmedia(event=event, name="Slides", type="PDF")
                            verb = "Created"
                        else:
                            verb = "Updated"
                        uri = u"/" + os.path.relpath(media_path, settings.BASE_DIR)
                        em.uri = uri
                        em.visible = True
                        em.save()
                        event.save()
                    else:
                        em = Eventmedia.objects.filter(event=event, name="Spotlight Slides", type="PDF")
                        if em:
                            messages.success(request, u"Removed existing links to this upload from the <a target='_blank' href='{0}'>schdule for this event &raquo;</a>. If this was not intended, check the 'downloadable' checkbox and re-upload your file.".format(event.get_schedule_url()))
                            em.delete()
                            event.save()
    except Exception as e:
        log.warning(traceback.format_exc())
        messages.error(request, u"An error occurred, possibly a missing presenter." )


def paper_detail(request, year, eventid):

    confInfo = getConfInfo(request, year=year)

    paper = Events.objects.filter(
        pk=eventid, session__conference__id=year).first()

    urls = get_urls()

    meeting_over = now().date() > Conferences.objects.get(pk=settings.CURRENT_CONFERENCE).enddate + timedelta(days=2)

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


    if request.user.is_authenticated and paper:
        request_user_is_author = paper.eventspeakers_set.filter(speaker__in=request.user.get_all_user_links()).exists()

        if request_user_is_author:
            slideUploadForm = SlideUploadForm(event=paper)
            if not paper.location:
                paper.location = "Virtual"  #This is required to get a slide path or to get the url to a slide.  Location cannot be empty


    if request.method == "POST":
        
        process_slide_upload(request, paper)


    return(render(request, "virtual/paper_detail.html", locals()))


def tutorial_detail(request, year, eventid):

    confInfo = getConfInfo(request, year=year)

    tutorial = Events.objects.filter(
        pk=eventid, session__conference__id=year).first()  #tutorial is actually a tutorial

    urls = get_urls()

    access_granted = get_access(request, year)

    meeting_over = now().date() > Conferences.objects.get(pk=settings.CURRENT_CONFERENCE).enddate + timedelta(days=2)

    """Create or get the rocketchat channel for this tutorial and make sure the request user has a rocketchat account"""
    from rocketchat_conferences import helpers as rch

    rci = rch.get_active_rocketchat_conf_inst_obj()

    if access_granted and tutorial and rci:

        rcu = rch.find_or_create_user(request.user)

        try:

            event_channel = rch.find_or_create_events_channel(tutorial)

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


    if request.user.is_authenticated and tutorial:
        request_user_is_author = tutorial.eventspeakers_set.filter(speaker__in=request.user.get_all_user_links()).exists()

        if request_user_is_author:
            slideUploadForm = SlideUploadForm(event=tutorial)
            if not tutorial.location:
                tutorial.location = "Virtual"  #This is required to get a slide path or to get the url to a slide.  Location cannot be empty


    if request.method == "POST":
        
        process_slide_upload(request, tutorial)


    return(render(request, "virtual/tutorial_detail.html", locals()))


def invited_talk_detail(request, year, eventid):

    confInfo = getConfInfo(request, year=year)

    talk = Events.objects.filter(
        pk=eventid, session__conference__id=year).first()  #talk is actually a talk

    urls = get_urls()

    access_granted = get_access(request, year)

    meeting_over = now().date() > Conferences.objects.get(pk=settings.CURRENT_CONFERENCE).enddate + timedelta(days=2)

    """Create or get the rocketchat channel for this talk and make sure the request user has a rocketchat account"""
    from rocketchat_conferences import helpers as rch

    rci = rch.get_active_rocketchat_conf_inst_obj()

    if access_granted and talk and rci:

        rcu = rch.find_or_create_user(request.user)

        try:

            event_channel = rch.find_or_create_events_channel(talk)

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

    if request.user.is_authenticated and talk:
        request_user_is_author = talk.eventspeakers_set.filter(speaker__in=request.user.get_all_user_links()).exists()

        if request_user_is_author:
            slideUploadForm = SlideUploadForm(event=talk)
            if not talk.location:
                talk.location = "Virtual"  #This is required to get a slide path or to get the url to a slide.  Location cannot be empty


    if request.method == "POST":

        process_slide_upload(request, talk)


    return(render(request, "virtual/invited_talk_detail.html", locals()))

def events(request, year, event_type):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    urls = get_urls()

    tz_name, tz_offset = get_timezone()

    events = Events.objects.filter(
        session__conference__id=year, type__istartswith=event_type)  #This should probably be iexact but we have AffinityWorkshops which are workshops.  



    if event_type == "paper":
        events = events.order_by("?")
    else:
        events = events.order_by("starttime")

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

    tz_name, tz_offset = get_timezone()

    urls = get_urls()

    wks = Events.objects.filter(
        session__conference__id=year, type__icontains="Workshop").order_by("?")

    return(render(request, "virtual/workshops.html", locals()))




def workshop_detail(request, year, eventid):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    urls = get_urls()

    workshop = Events.objects.filter(pk=eventid).first()

    meeting_over = now().date() > Conferences.objects.get(pk=settings.CURRENT_CONFERENCE).enddate + timedelta(days=2)

    if workshop:
        wkapp = workshop.get_application()
        if wkapp:
            
            wkapp = wkapp[0]  #This returns a list not queryset

            meeting_opens = Events.objects.exclude(starttime=None).order_by("starttime").first().starttime - timedelta(days=2)  #Show zoom links the day before the meeting starts
            meeting_closes = Events.objects.exclude(endtime=None).order_by("endtime").last().endtime + timedelta(days=2)  #Show zoom links the day before the meeting starts

            show_zoom_links = now() > meeting_opens and now() < meeting_closes
            show_zoom_links = True

            show_start_link = wkapp.organizers.filter(pk=request.user.pk).exists()

        else:
            wkapp = None



    from rocketchat_conferences import helpers as rch

    rci = rch.get_active_rocketchat_conf_inst_obj()

    if access_granted and workshop and rci:

        rcu = rch.find_or_create_user(request.user)

        try:

            event_channel = rch.find_or_create_events_channel(workshop)

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

    return(render(request, "virtual/workshop_detail.html", locals()))



def socials(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    tz_name, tz_offset = get_timezone()

    urls = get_urls()
    
    return(render(request, "virtual/socials.html", locals()))

def awards(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    tz_name, tz_offset = get_timezone()

    urls = get_urls()

    from rocketchat_conferences import helpers as rch

    rci = rch.get_active_rocketchat_conf_inst_obj()

    if access_granted and rci:

        rcu = rch.find_or_create_user(request.user)

        try:

            event_channel = rch.find_or_create_channel("awards-ceremony", [])

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
    
    return(render(request, "virtual/awards.html", locals()))

def miniconf_calendar(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    tz_name, tz_offset = get_timezone()

    urls = get_urls()
    
    return(render(request, "virtual/miniconf-calendar.html", locals()))


def calendar(request, year):

    begin = time.time()

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    tz_name, tz_offset = get_timezone()

    user_tz = pytz.timezone(tz_name)

    urls = get_urls()

    siso = Events.objects.filter(session__conference__id=year, show_in_schedule_overview=True)  #sis show_in_schedule_overview

    for event in siso:
        event.starttime = user_tz.normalize(event.starttime)

    days = siso.values_list("starttime__date", flat=True)

    data = {}
    for day in days:
        events = siso.filter(starttime__date=day)
        data[day] = events

    print(time.time() - begin)

    return(render(request, "virtual/calendar.html", locals()))


def townhall(request, year):

    confInfo = getConfInfo(request, year=year)

    access_granted = get_access(request, year)

    meeting_over = now().date() > Conferences.objects.get(pk=settings.CURRENT_CONFERENCE).enddate + timedelta(days=2)

    tz_name, tz_offset = get_timezone()

    urls = get_urls()

    event = Events.objects.filter(session__conference__id=settings.CURRENT_CONFERENCE, name__istartswith="Town Hall").order_by("starttime").first()


    from rocketchat_conferences import helpers as rch

    rci = rch.get_active_rocketchat_conf_inst_obj()



    if access_granted and rci:

        rcu = rch.find_or_create_user(request.user)

        try:

            event_channel = rch.find_or_create_channel("townhall", [])

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
    
    return(render(request, "virtual/townhall-detail.html", locals()))