import time
import redis
import requests
import json

from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SECRET_KEY'] = '7110c8ae51a4b5af97be65fghl50fgdfjk4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe'
cache = redis.Redis(host='redis', port=6379)

class JobForm(FlaskForm):
    job = StringField('job', validators=[DataRequired()])
    submit = SubmitField('Search')

def add_cache_key(data_job, key):
    retries = 5
    
    while True:
        try:
            cache.set(key, json.dumps(data_job))
            cache.expire(key, 300)

            return True
        except BaseException as exc:
            if retries == 0:
                raise exc

            retries -= 1
            time.sleep(0.5)

def get_data_job(job):
    job_search = job.replace(' ', '+')

    if cache.exists(job_search) != 0:
        return json.loads(cache.get(job_search))

    url = 'https://stackoverflow.com/jobs?q=' + job_search + '&r=true&sort=y'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    results = soup.find_all('div', class_='-job')

    for result in results:
        if '_featured' not in result.get('class'):
            h2 = result.find('h2')
            link = 'https://stackoverflow.com' + h2.find('a')['href']
            enterprise = result.find('h3').find('span').get_text().rstrip()
            position = h2.find('a').text

            for li in result.find_all('li'):
                if li.has_attr('title'):
                    salary = li['title']

    data_job = {"link":link, "enterprise":enterprise, "position":position, "salary":salary}
    add_cache_key(data_job, job_search)        

    return data_job

@app.route('/', methods=["GET", "POST"])
def index():
    form = JobForm()

    if form.validate_on_submit():
        job = form.job.data
        data_job_dict = get_data_job(job)
        
        return render_template('index.html', job=data_job_dict, form=form)

    return render_template('index.html', form=form)