# Google Calendar Availability Formatter

This tool is designed to be a helpful tool for formatting your calendar availability for easy pasting into emails.
Now, whenever someone asks you "when are you free next week?", you can easily load up this tool and copy the
formatted availability into your email without worrying that you missed an appointment.

## Installation Requirements
This tool requires Python 2.6+, with the following dependencies:
```pip install pyperclip tkcalendar```

To interface with Google Calendar's API, you'll also need to follow the Prerequisite steps and Step 1 in the
[Google Calendar Python Quickstart Guide](https://developers.google.com/calendar/api/quickstart/python). 
Rename the "client-secret-***.json" file you receive as "credentials.json" and place it in this folder.

On line 19 of ```main.py```, you should also replace the calendar ID with your own Google Calendar's
calendar ID. You can find where the calendar ID is located 
[via this tutorial](https://docs.simplecalendar.io/find-google-calendar-id/).

## Interface
![Picture of the GCal Availability tool interface](images/gcal_availability_interface.png)

1) The top row allows you to select which days of the week you want to include in your availability listing. By
default, a Monday-Friday weekday is selected, although you can change this on lines 203-204 in the code.
   
2) The second row allows you to select the start date and end date of your availability listing.

3) The third row allows you to select your workday's start and end times.

4) The fourth row (below the horizontal line) allows you to select how many minutes of buffer you want
before and after meetings, e.g. for walking in between locations.
   
5) The fifth row allows you to select the minimum time interval posted on your availability listing. For 
example, the default 60 minutes ensures that no time slots under an hour are listed. This is for brevity 
   and clarity, since otherwise you could have lots of 15 or 30 minutes time intervals between meetings 
   that clutter up your availability posting.
   
6) The sixth row is the output box, which allows you to copy the resultant availability or inspect it
for errors. The availability will be copied to your clipboard automatically for convenience, however.
   
7) Finally, click the button at the bottom to begin the process!

