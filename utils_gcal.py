from datetime import datetime, timedelta, date, time, timezone
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pyperclip

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def subtract_time(t1, t2):
    d1 = datetime.combine(datetime.today(), t1)
    d2 = datetime.combine(datetime.today(), t2)
    return d1 - d2


def get_events(calendar_id, startTime, endTime):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
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
    events_result = service.events().list(calendarId=calendar_id,
                                          timeMin=startTimeStr, timeMax=endTimeStr, singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])
    return events


def parse_availability(event_list, start_date, end_date, start_time, end_time, buffer_before, buffer_after, minimum_time, allowed_days):
    buffer_before = timedelta(minutes=buffer_before)
    buffer_after = timedelta(minutes=buffer_after)
    minimum_time = timedelta(minutes=minimum_time)
    start_times = []
    end_times = []
    for event_itr in range(len(event_list)):
        if 'dateTime' in event_list[event_itr]['start'] and 'dateTime' in event_list[event_itr]['end']:
            start_times.append(datetime.strptime(event_list[event_itr]['start'].get('dateTime'), '%Y-%m-%dT%H:%M:%S%z') - buffer_before)
            end_times.append(datetime.strptime(event_list[event_itr]['end'].get('dateTime'), '%Y-%m-%dT%H:%M:%S%z') + buffer_after)

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
                if (itr < len(intervals) - 1) and intervals[itr+1][0] == day:
                    out += ','
                elif 1 < itr < len(intervals) and intervals[itr][0] == day and intervals[itr-2][0] == day:
                    out += ', and'
                elif itr < len(intervals) and intervals[itr][0] == day:
                    out += ' and'

        if i != diff:
            out += '; '
    return out


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    startTime = datetime.now()
    endTime = datetime.now() + timedelta(days=10)
    endTime = endTime.replace(hour=23, minute=59, second=59)
    dayStartTime = time(9, 0, 0)
    dayEndTime = time(17, 0, 0)

    events = get_events('al4md8n2a6jlkno1hd71t8blco@group.calendar.google.com', startTime, endTime)
    intervals = parse_availability(events, startTime, endTime, dayStartTime, dayEndTime, 0, 0, 60)
    availability_str = format_availability(intervals, 0, dayStartTime, dayEndTime)

    pyperclip.copy(availability_str)
    print(availability_str)


if __name__ == '__main__':
    main()
