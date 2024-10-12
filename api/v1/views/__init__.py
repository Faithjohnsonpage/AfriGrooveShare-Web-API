#!/usr/bin/env python3
"""Blueprint for API """
from flask import Blueprint

app_views = Blueprint('app_views', __name__)


from api.v1.views.index import *
from api.v1.views.users import *
from api.v1.views.artist import *
from api.v1.views.album import *
from api.v1.views.genre import *
from api.v1.views.music import *
from api.v1.views.playlist import *
from api.v1.views.news import *
from api.v1.views.admin import *
