from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(User, UserAdmin)

class CourseOfferingInline(admin.TabularInline):
    model = CourseOffering
    show_change_link = True


class SlotInline(admin.TabularInline):
    model = Slot
    show_change_link = True


class RequestSlotsInline(admin.TabularInline):
    model = Request.slots.through
    show_change_link = True


@admin.register(Quarter)
class QuarterAdmin(admin.ModelAdmin):
    inlines = [
        CourseOfferingInline
    ]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [
        CourseOfferingInline
    ]

@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    inlines = [
        SlotInline
    ]

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_filter = ['course_offering', 'format']
    #pass

@admin.register(ActiveRequest)
class ActiveRequestAdmin(admin.ModelAdmin):
    pass

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    inlines = [
        RequestSlotsInline
    ]
    exclude = ('slots',)

