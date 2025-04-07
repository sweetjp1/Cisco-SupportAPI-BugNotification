from flask import Flask
from flask import render_template, flash, redirect, request
from forms import PlatformForm, LogForm, ConfigForm, EmailForm
from dotenv import load_dotenv, set_key
import os, glob
import main

#Make Log Page have Run Now Button


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('API_SECRET')

@app.route('/')
def hello_world():
    return '<p>Hello World</p>'

@app.route('/<input>')
def hello_input(input=None):
    return render_template('index.html',input=input)

@app.route('/platform', methods=['GET','POST'])
def platform_config():
    form = PlatformForm()

    #on submit, delete the existing .bug files, overwrite platform.cfg with new platforms, then run main.py to initialize our bug lists.
    if form.validate_on_submit():
        for f in glob.glob('*.bug'):
            os.remove(f)
        f = open('platform.cfg', 'w')
        f.write(form.platform_file.data)
        f.close()
        
        flash('File Saved')
        return redirect('/platform')
    
    #regular view (no post): load the content of platform.cfg
    try:
        platforms = open('platform.cfg', 'r')
        platform_read = platforms.read()
        platforms.close()

        form.platform_file.data=platform_read
        platform_list = platform_read.splitlines()
        return render_template('platform.html',platform_list=platform_list, form=form)

    except:
        flash('Error opening platform.cfg')

@app.route('/config', methods=['GET','POST'])
def config():
    api_form= ConfigForm()
    email_form = EmailForm()
    path='.env'
    load_dotenv(path, override=True)

    if api_form.validate_on_submit():
        set_key(path, 'API_KEY', api_form.key.data)
        set_key(path, 'API_SECRET', api_form.client_secret.data)
        flash('API Config Saved')
        return redirect('/config')
    

    if email_form.validate_on_submit():
        set_key(path, 'EMAIL_LIST', email_form.email_list.data)
        flash('Notification Emails Saved')
        return redirect('/config')
    
    #OSENVIRON DOES NOT REFRESH. MAKE THIS A SEPARATE FILE.

    emails=os.getenv("EMAIL_LIST")
    email_form.email_list.data = emails

    return render_template('config.html', emails=emails, api_form=api_form, email_form = email_form)


@app.route('/log', methods=['GET','POST'])
def log():
    form = LogForm()
    if form.validate_on_submit():
        if 'delete' in request.form:
            open('main.log', 'w').close()
            flash('Log Cleared')
            return redirect('/log')
        elif 'run' in request.form:
            main.main()
            flash('Run Successful')
            return redirect('/log')
    try:
        logfile = open('main.log', 'r')
        logfile_read = logfile.read()
        logfile.close()
        return render_template('log.html',logfile=logfile_read,form=form)

    except:
        print('Error opening platform.cfg')