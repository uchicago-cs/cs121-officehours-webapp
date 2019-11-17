#!/usr/bin/python3

import os, django, sys

sys.path.append("../")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()


import officehours.models as models

aut19, created = models.Quarter.objects.get_or_create(ais_num = 2198,
                                                      year = 2019,
                                                      quarter = "aut")


cs121, created = models.Course.objects.get_or_create(ais_num = 56311,
                                                     subject = "CMSC",
                                                     catalog_code = 12100,
                                                     name = "Computer Science with Applications 1")

cs121_aut_19, created = models.CourseOffering.objects.get_or_create(course = cs121,
                                                                    quarter = aut19,
                                                                    url_slug = "cmsc12100-aut-19")
