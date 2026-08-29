#!/bin/sh
# Terminal commands to set up this project's Python environment and
# install every dependency from requirements.txt individually via pip.

py -3.11 -m venv venv
venv\Scripts\Activate.ps1

pip install Flask==3.0.3
pip install Flask-SQLAlchemy==3.1.1
pip install Flask-Login==0.6.3
pip install Flask-WTF==1.2.1
pip install email_validator==2.2.0
pip install requests==2.34.2
pip install python-dotenv==1.0.1
