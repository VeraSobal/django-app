from datetime import datetime
from pathlib import Path
from django.shortcuts import render

import pandas as pd
from pathlib import Path

template_path = Path("ordertrack_app")


def index(request):
    context = {"now": datetime.now()}
    return render(request, template_path/"index.html",  context=context)
