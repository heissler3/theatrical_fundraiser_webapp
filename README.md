
# Theatrical Fundraiser Web App

This was a prototype written for a local theater group's fundraiser with the intention of storing and retrieving donor information and their pledges.

The intended gimmick was that the attendees would be assigned a character name upon entry (we chose to go with Shakespearean characters), and during the pledge drive, a screen would display a chart grouped by the plays the characters were from, with a running total for each play.

The server side of the app is written in python using Flask.  [Chart.js](https://www.chartjs.org) is used for the progress page.

Styling was done by **Kathryn Murrell**, working from template **"Escape Velocity"** from [HTML5 UP](https://html5up.net/).  Coding by **Henry Eissler** (except for the Chart.js).

#### <u>To-Do:</u>
+ Error Checking on New Donor entries
+ Actions on Donor Review page, such as:
    + Re-assign character
    + Edit contact information
    + Print badge ("Hello, my name is...")
+ Reflect Play name in Donor Review
+ Replace randomize color palette with fixed, styled palette
+ Error checking everywhere
