from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator


class Quarter(models.Model):
    ais_num = models.PositiveIntegerField(primary_key=True)
    year = models.PositiveIntegerField()
    quarter = models.CharField(max_length=3, choices = [("aut", "Autumn"),
                                                        ("win", "Winter"),
                                                        ("spr", "Spring"),
                                                        ("sum", "Summer")])

    class Meta:
        unique_together = (("year", "quarter"),)

    def __str__(self):
        return "{} {}".format(self.get_quarter_display(), self.year)

    @property
    def academic_year(self):
        if self.quarter in ("sum", "aut"):
            return "{}/{:02d}".format(self.year, (self.year % 100) + 1)
        elif self.quarter in ("win", "spr"):
            return "{}/{:02d}".format(self.year - 1, (self.year % 100))


class Course(models.Model):
    ais_num = models.PositiveIntegerField(primary_key=True)
    subject = models.CharField(max_length=4)
    catalog_code = models.IntegerField(validators=[MinValueValidator(10000),
                                                   MaxValueValidator(99999)])
    name = models.CharField(max_length=256)

    def __str__(self):
        return "{} {} - {} ({})".format(self.subject, self.catalog_code, self.name, self.ais_num)


class CourseOffering(models.Model):
    STATE_OPEN = 10
    STATE_CLOSED = 20

    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE)
    archived = models.BooleanField(default=False)
    state = models.PositiveIntegerField(choices = [(STATE_OPEN,   "Open"),
                                                   (STATE_CLOSED, "Closed")],
                                        default = STATE_CLOSED)

    url_slug = models.CharField(max_length=256, unique=True)

    servers = models.ManyToManyField(User, blank=True)

    class Meta:
        unique_together = (("course", "quarter"),)

    def __str__(self):
        return "{} {} - {} ({})".format(self.subject, self.catalog_code, self.name, self.quarter)

    @property
    def ais_num(self):
        return self.course.ais_num

    @property
    def subject(self):
        return self.course.subject

    @property
    def catalog_code(self):
        return self.course.catalog_code

    @property
    def name(self):
        return self.course.name

    def get_active_request(self, user):
        reqs = self.request_set.filter(students = user, state__in = Request.ACTIVE_STATES)

        assert len(reqs) <= 1

        if len(reqs) == 0:
            return None
        else:
            return reqs[0]


class Slot(models.Model):
    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)

    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=64)

    def __str__(self):
        return "{} ({})".format(self.date, self.interval)

    @property
    def interval(self):
        start = self.start_time.strftime("%I:%M %p")
        end = self.end_time.strftime("%I:%M %p")
        return "{} - {}".format(start, end)

class Request(models.Model):
    STATE_PENDING = 10
    STATE_SCHEDULED = 20
    STATE_INPROGRESS = 30
    STATE_COMPLETED = 40
    STATE_NOSHOW = 50
    STATE_COULDNOTSEE = 60
    STATE_CANCELLED = 70
    STATE_INVALID = 80

    ACTIVE_STATES = (STATE_PENDING, STATE_SCHEDULED, STATE_INPROGRESS)

    TYPE_REGULAR = 10
    TYPE_EXPRESS = 20

    course_offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE)
    students = models.ManyToManyField(User, related_name="requests")
    server = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="assigned_requests")
    date = models.DateField()

    slots = models.ManyToManyField(Slot)
    actual_slot = models.ForeignKey(Slot, on_delete=models.CASCADE, blank=True, null=True, related_name="assigned_slot")

    service_start_time = models.TimeField(blank=True, null=True)
    service_end_time = models.TimeField(blank=True, null=True)

    state = models.PositiveIntegerField(choices = [(STATE_PENDING,     "Pending"),
                                                   (STATE_SCHEDULED,   "Scheduled"),
                                                   (STATE_INPROGRESS,  "In Progress"),
                                                   (STATE_COMPLETED,   "Completed"),
                                                   (STATE_NOSHOW,      "No-show"),
                                                   (STATE_COULDNOTSEE, "Could not schedule"),
                                                   (STATE_CANCELLED,   "Cancelled"),
                                                   (STATE_INVALID,     "Invalid"),
                                                   ],
                                        default = STATE_PENDING)

    type = models.PositiveIntegerField(choices = [(TYPE_REGULAR, "Regular"),
                                                  (TYPE_EXPRESS, "Express")
                                                 ],
                                        default = TYPE_REGULAR)

    description = models.TextField()

    @property
    def is_active(self):
        return self.state in Request.ACTIVE_STATES

    def get_state_class(self):
        if self.state in (Request.STATE_PENDING,):
            return "btn-warning"
        elif self.state in (Request.STATE_SCHEDULED, Request.STATE_INPROGRESS):
            return "btn-success"
        elif self.state in (Request.COMPLETED,):
            return "btn-info"
        elif self.state in (Request.STATE_NOSHOW, Request.STATE_COULDNOTSEE, Request.STATE_CANCELLED, Request.STATE_INVALID):
            return "btn-danger"
        else:
            return "btn-info"


