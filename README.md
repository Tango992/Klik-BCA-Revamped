# Klik BCA Revamped Prototype - CS50x Final Project
![Transfer List Page](/assets/md/trf_page.png)

## Description:

### Background:
> As an experimental project for [CS50x (Harvard's Introduction to Computer Science)](https://cs50.harvard.edu/x/2023/), I want to reimagine internet banking that we currently have, that is to change the 6 digit pin into a timed-based one time pin or OTP to provide more security. This website will also give a more modern look than the existing [BCA Internet Banking](https://www.klikbca.com/).

### Technologies used:
* Bootstrap
* Flask
* HTML
* CSS
* SQL
* JavaScript
* Google OAuth
* OTP

## Highlights
* __One-Time-Password.__ This is used througout login and all vital activities.
* __Google Login.__ Although it seems counterintuitive to link a social profile with a banking account, turns out logging in with google means you don't have to type any more password. On top of that, the site will also ask for an additional OTP that will only be generated during registration.
* __Theme Toggler.__ Made possible utilizing Bootstrap's light and dark mode and storing it to site's session with JavaScript.

## Setup
1. Clone this repository.
2. Activate virtual environment with: 
```
python3 -m venv .venv
```
3. Install dependencies: 
```
pip install -r requirements.txt
```
4. Run the following command to set the Flask environment variable:
```
export FLASK_APP=application.py
```
5. Run command `flask run` to open on localhost

## Current Limitations & Possible Improvements
Because it's a prototype, users can only transfer between BCA account number registered in the SQL database. The option to transfer to other banks are greyed out, since there are no way to validate the account number.