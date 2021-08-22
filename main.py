import tkinter as tk
from tkinter.ttk import Combobox, Separator, Scrollbar, Entry
import tkcalendar
from datetime import timedelta, datetime, timezone, date, time
# from utils_gcal import get_events, parse_availability, format_availability
import pyperclip

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# import pyperclip

# Go to Google Calendar > Calendar Settings > Look up Calendar ID
calendars = ["primary",
             "al4md8n2a6jlkno1hd71t8blco@group.calendar.google.com"]
# calendars = ["al4md8n2a6jlkno1hd71t8blco@group.calendar.google.com"]  # Currently only supports one calendar

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']


def subtract_time(t1, t2):
    d1 = datetime.combine(datetime.today(), t1)
    d2 = datetime.combine(datetime.today(), t2)
    return d1 - d2


def get_events(calendar_ids, startTime, endTime):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Trying refresh")
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    startTimeStr = startTime.isoformat()
    endTimeStr = endTime.isoformat()
    all_events = []
    for calendar_id in calendar_ids:
        events_result = service.events().list(calendarId=calendar_id,
                                              timeMin=startTimeStr, timeMax=endTimeStr, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])
        all_events.extend(events)
    all_events.sort(key=lambda event: datetime.strptime(event['start'].get('dateTime'), '%Y-%m-%dT%H:%M:%S%z'))
    return all_events


def parse_availability(event_list, start_date, end_date, start_time, end_time, buffer_before, buffer_after,
                       minimum_time, allowed_days):
    buffer_before = timedelta(minutes=buffer_before)
    buffer_after = timedelta(minutes=buffer_after)
    minimum_time = timedelta(minutes=minimum_time)
    start_times = []
    end_times = []
    for event_itr in range(len(event_list)):
        if 'dateTime' in event_list[event_itr]['start'] and 'dateTime' in event_list[event_itr]['end']:
            start_times.append(datetime.strptime(event_list[event_itr]['start'].get('dateTime'),
                                                 '%Y-%m-%dT%H:%M:%S%z') - buffer_before)
            end_times.append(
                datetime.strptime(event_list[event_itr]['end'].get('dateTime'), '%Y-%m-%dT%H:%M:%S%z') + buffer_after)

    # start_time = datetime.strptime(start_time, "%I:%M%p").time()
    # end_time = datetime.strptime(end_time, "%I:%M%p").time()

    event_itr = 0
    if type(start_date) == datetime:
        start_date = start_date.date()
        end_date = end_date.date()

    diff = (end_date - start_date).days
    intervals = []
    for i in range(diff + 1):
        day = start_date + timedelta(days=i)
        start = start_time
        new_day = False
        while event_itr < len(start_times) and start_times[event_itr].date() == day:
            event_start_time = start_times[event_itr].time()
            event_end_time = end_times[event_itr].time()
            end = min(event_start_time, end_time)

            # Removes events that start at start_time and enforces the minimum time limit
            # print(day, start, end, subtract_time(end, start), minimum_time, subtract_time(end, start) >= minimum_time)
            if start < end and subtract_time(end, start) >= minimum_time and allowed_days[day.weekday()]:
                intervals.append((day, start, end))
            event_itr += 1

            if event_end_time < end_time:  # Confirms that there's still time left in the day
                start = event_end_time
                new_day = False
            else:  # Continue onto the next day
                start = start_time
                new_day = True
        if not new_day and subtract_time(end_time, start) >= minimum_time and allowed_days[day.weekday()]:
            intervals.append((day, start, end_time))
    return intervals


def format_availability(intervals, format, start_time, end_time):
    start_date = intervals[0][0]
    end_date = intervals[-1][0]
    # start_time = datetime.strptime(start_time, "%I:%M%p").time()
    # end_time = datetime.strptime(end_time, "%I:%M%p").time()
    noon = time(12, 0, 0)

    diff = (end_date - start_date).days
    out = ""
    itr = 0
    for i in range(diff + 1):
        day = start_date + timedelta(days=i)

        if intervals[itr][0] != day:  # not an allowed day
            continue

        if i == diff:
            out += 'and '

        free_all_day = (start_time == intervals[itr][1]) and (end_time == intervals[itr][2])
        if free_all_day:
            out += 'anytime '
            itr += 1
        out += 'on ' + day.strftime("%A (") + day.strftime("%m/").lstrip("0") + day.strftime("%d)").lstrip("0")

        if not free_all_day:
            while itr < len(intervals) and intervals[itr][0] == day:
                interval_start_time = intervals[itr][1]
                interval_end_time = intervals[itr][2]
                out += ' '
                if interval_start_time < noon and interval_end_time < noon:
                    if interval_start_time.minute == 0:
                        out += interval_start_time.strftime("%I").lstrip("0")
                    else:
                        out += interval_start_time.strftime("%I:%M").lstrip("0")
                    out += '-'
                    if interval_end_time.minute == 0:
                        out += interval_end_time.strftime("%Iam").lstrip("0").lstrip("0")
                    else:
                        out += interval_end_time.strftime("%I:%Mam").lstrip("0").lstrip("0")
                elif interval_start_time < noon <= interval_end_time:
                    if interval_start_time.minute == 0:
                        out += interval_start_time.strftime("%Iam").lstrip("0")
                    else:
                        out += interval_start_time.strftime("%I:%Mam").lstrip("0")
                    out += '-'
                    if interval_end_time.minute == 0:
                        out += interval_end_time.strftime("%Ipm").lstrip("0")
                    else:
                        out += interval_end_time.strftime("%I:%Mpm").lstrip("0")
                else:
                    if interval_start_time.minute == 0:
                        out += interval_start_time.strftime("%I").lstrip("0")
                    else:
                        out += interval_start_time.strftime("%I:%M").lstrip("0")
                    out += '-'
                    if interval_end_time.minute == 0:
                        out += interval_end_time.strftime("%Ipm").lstrip("0")
                    else:
                        out += interval_end_time.strftime("%I:%Mpm").lstrip("0")

                itr += 1
                if (itr < len(intervals) - 1) and intervals[itr + 1][0] == day:
                    out += ','
                elif 1 < itr < len(intervals) and intervals[itr][0] == day and intervals[itr - 2][0] == day:
                    out += ', and'
                elif itr < len(intervals) and intervals[itr][0] == day:
                    out += ' and'

        if i != diff:
            out += '; '
    return out


#####################################################################################################################
# Instantiate GUI
#####################################################################################################################
window = tk.Tk()
window.title("Google Calendar Availability Generator")
width, height = 400, 450
window.geometry(str(width) + 'x' + str(height))

#####################################################################################################################
# Create days of the week checkboxes
#####################################################################################################################
WEEKDAYS = ["S", "M", "T", "W", "Th", "F", "S"]
days = [tk.BooleanVar() for _ in range(7)]  # starts with Sunday
dayCheckboxes = [tk.Checkbutton(window, text=WEEKDAYS[i], variable=days[i]) for i in range(7)]
for i in range(7):
    dayCheckboxes[i].pack()
    dayCheckboxes[i].place(x=width*i//7 + 15, y=50)
    if 1 <= i <= 5:  # Turn on checkboxes Monday - Friday by default
        days[i].set(True)

#####################################################################################################################
# Create date range
#####################################################################################################################
dateStart = tkcalendar.DateEntry(window, width=10)
dateStart.pack(padx=10, pady=10)
dateStart.place(x=100, y=100)
tomorrow = datetime.today() + timedelta(days=1)
dateStart.set_date(tomorrow.date())  # Set default start day to tomorrow
dateStartLabel = tk.Label(window, text="Start Date:")
dateStartLabel.place(x=35, y=100)

dateEnd = tkcalendar.DateEntry(window, width=10)
dateEnd.pack(padx=10, pady=10)
dateEnd.place(x=260, y=100)
timeUntilNextFriday = (6 - datetime.today().weekday()) + 5  # Set default end date to next Friday
nextFriday = datetime.today() + timedelta(days=timeUntilNextFriday)
dateEnd.set_date(nextFriday.date())
dateEndLabel = tk.Label(window, text="End Date:")
dateEndLabel.place(x=195, y=100)

#####################################################################################################################
# Create time of day start/end
#####################################################################################################################
midnight = datetime.now()
midnight = midnight.replace(hour=0, minute=0)
times = [midnight + timedelta(minutes=m) for m in range(0, 24*60, 15)]
timesStr = [t.strftime("%I:%M%p") for t in times]

timeStart = tk.StringVar()
timeStartBox = Combobox(window, values=timesStr, textvariable=timeStart, width=10)
timeStart.set("09:00AM")
timeStartBox.pack()
timeStartBox.place(x=100, y=150)
timeStartLabel = tk.Label(window, text="Start Time:")
timeStartLabel.place(x=35, y=150)

timeEnd = tk.StringVar()
timeEndBox = Combobox(window, values=timesStr, textvariable=timeEnd, width=10)
timeEnd.set("05:00PM")
timeEndBox.pack()
timeEndBox.place(x=260, y=150)
timeEndLabel = tk.Label(window, text="End Time:")
timeEndLabel.place(x=195, y=150)

#####################################################################################################################
# Buffer times before and after events
#####################################################################################################################
separator = Separator(window, orient='horizontal')
separator.pack(fill='x')
separator.place(x=0, y=185, relwidth=1.0)
bufferBefore = tk.IntVar()
bufferBeforeBox = tk.Entry(window, textvariable=bufferBefore, width=10)
bufferBefore.set(0)
bufferBeforeBox.pack()
bufferBeforeBox.place(x=120, y=200)
bufferBeforeLabel = tk.Label(window, text="Buffer Before (min):")
bufferBeforeLabel.place(x=10, y=200)

bufferAfter = tk.IntVar()
bufferAfterBox = tk.Entry(window, textvariable=bufferAfter, width=6)
bufferAfter.set(0)
bufferAfterBox.pack()
bufferAfterBox.place(x=300, y=200)
bufferAfterLabel = tk.Label(window, text="Buffer After (min):")
bufferAfterLabel.place(x=195, y=200)

#####################################################################################################################
# Minimum Time Entry Box
#####################################################################################################################
minTime = tk.IntVar()
minTimeBox = tk.Entry(window, textvariable=minTime, width=10)
minTime.set(60)
minTimeBox.pack()
minTimeBox.place(x=160, y=250)
minTimeLabel = tk.Label(window, text="Minimum Time (min):")
minTimeLabel.place(x=30, y=250)

#####################################################################################################################
# Output
#####################################################################################################################
outputTextScrollbar = tk.Scrollbar(window)
outputText = tk.StringVar()
outputText.set('Output will be displayed here')
outputLabel = tk.Text(window, state='normal', yscrollcommand=outputTextScrollbar.set, width=40, height=4)
outputLabel.insert(tk.END, "Output will be displayed here")
outputLabel.pack()
outputLabel.place(x=30, y=300)
outputTextScrollbar.pack(side=tk.RIGHT, fill='y')


#####################################################################################################################
# Run button
#####################################################################################################################

def run():
    start_time = datetime.strptime(timeStart.get(), "%I:%M%p").time()
    end_time = datetime.strptime(timeEnd.get(), "%I:%M%p").time()
    start_date = datetime.strptime(dateStart.get(), "%m/%d/%y").date()
    end_date = datetime.strptime(dateEnd.get(), "%m/%d/%y").date()
    start = datetime.combine(start_date, start_time).replace(tzinfo=timezone(timedelta(hours=-7)))
    end = datetime.combine(end_date, end_time).replace(tzinfo=timezone(timedelta(hours=-7)))
    allowed_days = [d.get() for d in days[1:]] + [days[0].get()]  # datetime.weekday() puts Sunday last

    events = get_events(calendars, start, end)
    # for event in events:
    #     print(event)
    intervals = parse_availability(events, start_date, end_date, start_time, end_time,
                                   bufferBefore.get(), bufferAfter.get(), minTime.get(), allowed_days)
    # print(intervals)
    availability_str = format_availability(intervals, 0, start_time, end_time)

    pyperclip.copy(availability_str)
    print(availability_str)

    outputLabel.delete("1.0", "end")
    outputLabel.insert(tk.END, availability_str)


runButton = tk.Button(window, text="Find Availability", command=run)
runButton.pack()
runButton.place(x=160, y=400)

window.mainloop()
