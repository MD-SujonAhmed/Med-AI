import json
import os
from doctors.models import Doctor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "scripts", "dummy_data.json")

def run():
    with open(JSON_PATH) as f:
        data = json.load(f)

    for d in data["doctors"]:
        Doctor.objects.create(**d)

    print("Done")


"" """ python manage.py shell
from scripts.dummydata import run
run()"""