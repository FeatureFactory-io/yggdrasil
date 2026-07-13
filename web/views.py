"""HTMX web views."""

import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from graph.models import ChangeSet, Element

logger = logging.getLogger("yggdrasil.gui")


def welcome(request):
    from django.conf import settings
    return render(request, "web/welcome.html", {"revision": settings.GIT_REVISION})


@login_required
def view_browse(request):
    logger.info("screen=VIEW-BROWSE-1 user=%s", request.user.username)
    return render(request, "web/view_browse.html")


@login_required
def element_list(request):
    elements = Element.objects.filter(valid_to__isnull=True)[:50]
    count = elements.count()
    logger.info("screen=ELEMENT-LIST+FIND-1 user=%s count=%d", request.user.username, count)
    return render(request, "web/element_list.html", {"elements": elements})


@login_required
def changeset_list(request):
    changesets = ChangeSet.objects.all()[:50]
    logger.info("screen=CHANGESET-LIST+FIND-1 user=%s", request.user.username)
    return render(request, "web/changeset_list.html", {"changesets": changesets})


@login_required
def chat_assist(request):
    logger.info("screen=CHAT-ASSIST-1 user=%s", request.user.username)
    return render(request, "web/chat_assist.html")
