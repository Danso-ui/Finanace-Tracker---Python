from flask import Flask#, render_template, request
import datetime as dt

day = [
    'Monday', 'Tuesday',
    'Wednesday', 'Thursday',
    'Friday', 'Saturday', 'Sunday'
]
monthStr = [
    "January", "Febuary", "March",
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December"
]
now = dt.datetime.now()

# TODO: DATE, MONTH, YEAR
date = now.day
month = now.month
year = now.year

# TODO: MAIN WORK
app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)