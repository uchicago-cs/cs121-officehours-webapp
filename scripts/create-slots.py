import click
import datetime

import os, django, sys

sys.path.append(".")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()

import officehours.models as models

@click.command(name="create-slots")
@click.option('--date', type=click.DateTime())
@click.option('--start-time', type=click.DateTime(formats=["%H:%M"]))
@click.option('--end-time', type=click.DateTime(formats=["%H:%M"]))
@click.option('--slot-minutes', type=int)
@click.option('--format',  type=click.Choice(['in-person', 'online']), required=True)
@click.option('--room',  type=str)
@click.option('--update-db', '-u', is_flag=True)
@click.option('--yes', '-y', is_flag=True)
def cmd(date, start_time, end_time, slot_minutes, format, room, update_db, yes):
    start_time = datetime.datetime.combine(date, start_time.time())
    end_time = datetime.datetime.combine(date, end_time.time())
    slot_duration = datetime.timedelta(minutes=slot_minutes)

    if format == "in-person":
        if room is not None:
            print("ERROR: You must specify a room when creating in-person slots.")
            sys.exit(1)
        format = models.Slot.SLOT_INPERSON
    elif format == "online":
        if room is not None:
            print("ERROR: You cannot provide a room for online slots.")
            sys.exit(1)
        format = models.Slot.SLOT_ONLINE

    # TODO: Hard-coded
    cs121 = models.CourseOffering.objects.get(url_slug="cmsc12100-aut-21")

    num_slots = (end_time - start_time) / slot_duration

    if not num_slots.is_integer():
        print("ERROR: The provided interval would not be divided into a whole number of slots")
        sys.exit(1)

    num_slots = int(num_slots)

    date_str = "DATE {}".format(start_time.date())
    print(date_str)
    print("-" * len(date_str))
    cur_start = start_time
    slots = []
    for i in range(num_slots):
        slot_start = cur_start
        slot_end = cur_start + slot_duration

        slot_exists = models.Slot.objects.filter(course_offering=cs121,
                                                 date=slot_start.date(),
                                                 start_time=slot_start.time(),
                                                 end_time=slot_end.time(),
                                                 format=format
                                                )

        if slot_exists:
            exists_str = "(ALREADY EXISTS)"
        else:
            slot = models.Slot(course_offering=cs121,
                               date=slot_start.date(),
                               start_time=slot_start.time(),
                               end_time=slot_end.time(),
                               room=None,  # TODO: Hard-coded
                               format=format)
            slots.append(slot)
            exists_str = ""

        print("Slot #{}: {} - {}  {}".format(i+1, slot_start.time(), slot_end.time(), exists_str))

        cur_start = slot_end

    if update_db:
        print()
        print("You are going to update the website's database!")
        print()
        print("Are you sure you want to continue? (y/n): ", end=' ')

        if not yes:
            yesno = input()
        else:
            yesno = 'y'
            print('y')

        if yesno in ('y', 'Y', 'yes', 'Yes', 'YES'):
            print()
            for slot in slots:
                slot.save()
                print("Created slot", slot)
        print()


if __name__ == "__main__":
    cmd()