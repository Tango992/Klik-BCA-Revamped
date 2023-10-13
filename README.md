# Klik BCA Revamped Prototype - CS50x Final Project
![Transfer List Page](/assets/md/trf_page.png)

## Description:

### Background:
> As an experimental project for [CS50x (Harvard's Introduction to Computer Science)](https://cs50.harvard.edu/x/2023/), I wanted to reimagine internet banking that we currently have, that is to change the 6 digit pin into a __timed-based one time pin__ or OTP to provide more security. This website will also give a more modern look to the existing [BCA Internet Banking](https://www.klikbca.com/) but still keeping it clean and simple.

### Technologies used:

* Python
* Flask
* JavaScript
* OAuth 2.0
* Jinja
* HTML
* CSS
* SQL
* Bootstrap

## Highlights

* __One-Time-Password.__ This is used througout login and all vital activities.
* __Google Login.__ Although it seems counter intuitive to link a social profile with a banking account, but logging in with a Google account means you don't have to type any more password. On top of that, the site will also ask for an additional OTP that will only be generated during registration.
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

Because it's currently on a prototype state, users can only transfer between BCA account number registered in the SQL database. The option to transfer to other banks are greyed out, since there are no way to validate the account number.