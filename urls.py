from django.conf.urls import include, url
from django.urls import include, re_path, path
# Uncomment the next two lines to enable the admin:

from django.views.generic import TemplateView
import virtual.views

urlpatterns = [
    path("<int:year>", virtual.views.home, name="shorthome"),
    
    path("<int:year>/index.html", virtual.views.home, name="virtualhome"),
    
    path("<int:year>/paper_vis.html", virtual.views.paper_vis, name="paper_vis"),
    
    path("<int:year>/papers", virtual.views.papers, name="papers"),

    path("<int:year>/papers.html", virtual.views.papers, name="miniconf-papers"),


    path("<int:year>/calendar.html", virtual.views.miniconf_calendar, name="miniconf-calendar"),

    path("<int:year>/calendar", virtual.views.calendar, name="calendar"),

    path("<int:year>/awards.html", virtual.views.awards, name="miniconf-awards"),

    
    path("<int:year>/poster/<int:eventid>",
         virtual.views.paper_detail, name="virtual_paper_detail"),


    
    path("<int:year>/events/<event_type>",
         virtual.views.events, name="virtual_events"),

    path("<int:year>/workshop/<int:eventid>",
         virtual.views.workshop_detail, name="virtual_workshop_detail"),

    re_path(r"(?P<year>\d+)/affinity[\s_]*workshop/(?P<eventid>\d+)",
         virtual.views.workshop_detail, name="virtual_affinityworkshop_detail"),

    path("<int:year>/tutorial/<int:eventid>",
         virtual.views.tutorial_detail, name="virtual_tutorial_detail"),
    
    path("<int:year>/workshops", virtual.views.workshops, name="virtual_workshops"),
    
    path("ical/<int:eventid>/<int:number>", virtual.views.ical, name="ical"),



    re_path(r"(?P<year>\d+)/invited[\s_-]talk/(?P<eventid>\d*)",
     virtual.views.invited_talk_detail, name="virtual_invited_talk_detail"),

    path("<int:year>/test-of-time/<int:eventid>",
         virtual.views.paper_detail, name="test-of-time"),

    path("<int:year>/socials.html", virtual.views.socials, name="miniconf-socials"),
    path("<int:year>/social/<int:eventid>", virtual.views.socials, name="social_detail"),


    path("<int:year>/townhall", virtual.views.townhall, name="townhall"),    
    path("<int:year>/town-hall/<int:eventid>",
         virtual.views.townhall, name="townallwithid"),

    

    
]
