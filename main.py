import tkinter as tk
from tkinter.ttk import Combobox, Separator, Scrollbar, Entry
import tkcalendar
from datetime import timedelta, datetime, timezone
from utils_gcal import get_events, parse_availability, format_availability
import pyperclip

window = tk.Tk()
window.title("Google Calendar Availability Generator")
width, height = 400, 450
window.geometry(str(width) + 'x' + str(height))

# Go to Google Calendar > Calendar Settings > Look up Calendar ID
# calendars = ["primary",
#              "al4md8n2a6jlkno1hd71t8blco@group.calendar.google.com"]
calendars = ["al4md8n2a6jlkno1hd71t8blco@group.calendar.google.com"]  # Currently only supports one calendar
days = [tk.BooleanVar() for _ in range(7)]  # starts with Sunday

#####################################################################################################################
# Create days of the week checkboxes
#####################################################################################################################
WEEKDAYS = ["S", "M", "T", "W", "Th", "F", "S"]
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
# outputLabel = tk.Text(window, textvariable=outputText, state='readonly', yscrollcommand=outputTextScrollbar.set, width=width-80, height=100)
outputText.set('Output will be displayed here')
# outputLabel.pack()
# outputLabel.place(x=30, y=300)
# outputTextScrollbar.config(command=outputLabel.yview)
# outputTextScrollbar.pack(side=tk.RIGHT, fill='y')
# outputLabel = Entry(window, textvariable=outputText, state='readonly', width=width-80)
# outputTextScrollbar = Scrollbar(window, orient='horizontal', command=outputLabel.xview)
# outputLabel.config(xscrollcommand=outputTextScrollbar.set)
# outputLabel.place(x=30, y=300)
# # outputLabel.pack()
# outputTextScrollbar.pack(side=tk.RIGHT, fill='y')
# outputText = tk.StringVar()
outputLabel = tk.Text(window, state='normal', yscrollcommand=outputTextScrollbar.set, width=40, height=4)
outputLabel.insert(tk.END, "Output will be displayed here")
# outputText.set('Output will be displayed here')
outputLabel.pack()
outputLabel.place(x=30, y=300)
# outputTextScrollbar.config(command=outputLabel.yview)
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

    events = get_events(calendars[0], start, end)
    # for event in events:
    #     print(event)
    intervals = parse_availability(events, start_date, end_date, start_time, end_time,
                                   bufferBefore.get(), bufferAfter.get(), minTime.get(), allowed_days)
    # print(intervals)
    availability_str = format_availability(intervals, 0, start_time, end_time)

    pyperclip.copy(availability_str)
    # print(availability_str)
    # outputText.set(availability_str)
    outputLabel.delete("1.0", "end")
    outputLabel.insert(tk.END, availability_str)


runButton = tk.Button(window, text="Find Availability", command=run)
runButton.pack()
runButton.place(x=160, y=400)

window.mainloop()
