from django.conf.urls import include, url
from django.urls import include, re_path, path
# Uncomment the next two lines to enable the admin:

from django.views.generic import TemplateView
import virtual.views

urlpatterns = [
    path("<int:year>", virtual.views.home, name="shorthome"),
    
    path("<int:year>/index.html", virtual.views.home, name="virtualhome"),
    
    path("<int:year>/papers_vis", virtual.views.paper_vis, name="paper_vis"),
    
    path("<int:year>/papers", virtual.views.papers, name="papers"),

    path("<int:year>/papers.html", virtual.views.papers, name="miniconf-papers"),

    path("<int:year>/socials.html", virtual.views.socials, name="miniconf-socials"),
    
    path("<int:year>/poster/<int:eventid>",
         virtual.views.paper_detail, name="virtual_paper_detail"),
    
    path("<int:year>/events/<event_type>",
         virtual.views.events, name="virtual_events"),

    path("<int:year>/workshop/<int:eventid>",
         virtual.views.workshop_detail, name="virtual_workshop_detail"),

    path("<int:year>/affinityworkshop/<int:eventid>",
         virtual.views.workshop_detail, name="virtual_workshop_detail"),

    path("<int:year>/tutorial/<int:eventid>",
         virtual.views.tutorial_detail, name="virtual_tutorial_detail"),
    
    path("<int:year>/workshops", virtual.views.workshops, name="virtual_workshops"),
    
    path("ical/<int:eventid>/<int:number>", virtual.views.ical, name="ical"),

    re_path(r"(?P<year>\d+)/invited\stalk/(?P<eventid>\d*)",
     virtual.views.invited_talk_detail, name="virtual_invited_talk_detail"),


    path("<int:year>/invited%20talk/<int:eventid>",
         virtual.views.invited_talk_detail, name="virtual_invited_talk_detail"),
    
]
