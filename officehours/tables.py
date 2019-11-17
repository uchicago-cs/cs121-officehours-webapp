import django_tables2 as tables
import django_filters
from django.utils.html import format_html

from .models import Request


class RequestTable(tables.Table):

    class Meta:
        model = Request
        fields = ['pk', 'created_at', 'date', 'student', 'state', 'server', 'actual_slot']
        template_name = 'django_tables2/bootstrap.html'


