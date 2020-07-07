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
    path("<int:year>/paper/<int:eventid>",
         virtual.views.paper_detail, name="virtual_paper_detail"),
    path("<int:year>/events/<slug:event_type>",
         virtual.views.events, name="virtual_events"),
    path("<int:year>/workshops", virtual.views.workshops, name="virtual_workshops"),
    path("ical/<int:eventid>/<int:number>", virtual.views.ical, name="ical"),
]
