from flask import Flask
from flask import request, escape, render_template, redirect, url_for
from satellite_functions import satSite
from question import questionSite
#import git

app = Flask(__name__)

'''
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('./FunSite')
        origin = repo.remotes.origin
        repo.create_head('master',
    origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
        origin.pull()
        return '', 200
    else:
        return '', 400
'''

@app.route('/')
def index():
    return render_template('mainMenu.html')

def goToSatSite():
    return redirect(url_for('satSite'))

def goToQuestion():
    return redirect(url_for('questionSite'))

app.register_blueprint(satSite, url_prefix="/satSite")
app.register_blueprint(questionSite, url_prefix="/question")

#######################################################
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)