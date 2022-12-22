from flask import Flask
from flask import request, escape, render_template, redirect, url_for
import textImage
from datetime import datetime
from satellite_functions import satSite
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

app.register_blueprint(satSite, url_prefix="/satSite")

responses = {"Yes":"", "No":"",
             "8PM":"", "9PM":"", "Other":""}
nameList = []

angryGroup = "(-(-_-(-_(-_(-_-)_-)-_-)_-)_-)-)"

deniedResponse = """
            <div style="background-color: lightgrey;">
                <center>
                    <h1>Don't worry, I'm taking notes...</h1>
                    <div>
                        <li>
                            <div style="display: flex;
                                        flex-direction: column;
                                        align-items: center;
                                        justify-content: space-evenly;
                                        width: 30em;
                                        padding: 1em 2em;">
                                <h2>Hop on outta here</h2>
                                <p style="outline:1px solid black;">""" + textImage.duckWithHat + """</p>
                                <h1>You're not the intended audience</h1>
                                <p style="outline:1px solid black;">""" + textImage.pencilMan + """</p>
                                <h1>Quit it with the fucking scrolling</h1>
                                <p style="outline:1px solid black;">""" + textImage.susBoi + """</p>
                            </div>
                        </li>
                    </div>
                </center>
            </div>
                """

@app.route("/")
def index():
    inputName = str(escape(request.args.get("name_input", "")))
    print(inputName)
    if inputName.lower().__contains__("jack") or inputName.lower().__contains__("jaden") or inputName.lower().__contains__("daher") or inputName.lower().__contains__("jd"):
        nameList.append(inputName)
        return redirect(url_for('planPage'))
    elif inputName != '':
        nameList.append(inputName)
        return redirect(url_for('incorrectName'))
    else:
        return render_template('index.html')

@app.route("/watchMovie")
def correctName():
    EightPMResp = str(escape(request.args.get("EightPMResp", '')))
    responses["8PM"] = EightPMResp
    NinePMResp = str(escape(request.args.get("NinePMResp", '')))
    responses["9PM"] = NinePMResp
    otherResp = str(escape(request.args.get("otherResp", '')))
    responses["Other"] = otherResp
    print(f"EightPM: {EightPMResp} - NinePM: {NinePMResp} - Other: {otherResp}")
    if EightPMResp != '' or NinePMResp != '' or otherResp != '':
        return redirect(url_for("dubPage"))
    else:
        return render_template('correctNamePage.html')

@app.route("/incorrectName")
def incorrectName():
    appendFakeName()
    return deniedResponse

@app.route("/completed")
def dubPage():
    saveResponses()
    return render_template("dub.html")

@app.route("/about")
def aboutPage():
    return render_template("about.html")

@app.route("/planning")
def planPage():
    yes = str(escape(request.args.get("yesMovie", '')))
    responses["Yes"] = yes
    no = str(escape(request.args.get("noMovie", '')))
    responses["No"] = no
    if yes == 'on':
        return redirect(url_for('correctName'))
    elif no == 'on':
        return redirect(url_for('dubPage'))
    else:
        return render_template("yesNo.html")

def appendFakeName():
    with open("responses.txt", "a") as resp:
        curName = nameList[-1]
        resp.write(f"FakeName: {curName}\n")
        resp.close()

def saveResponses():
    with open("/home/jackslat/FunSite/responses.txt", "a") as resp:
        curName = nameList[-1]
        respYes = responses["Yes"]
        respNo = responses["No"]
        respEight = responses["8PM"]
        respNine = responses["9PM"]
        respOth = responses["Other"]
        now = datetime.now()
        curTime = now.strftime("%H:%M:%S")
        resp.write(f"Name: {curName}\nTime: {curTime}\nYes: {respYes}\tNo: {respNo}\n8PM: {respEight}\t9PM: {respNine}\tOther: {respOth}\n\n")
        resp.close()
    responses["Yes"] = ''
    responses["No"] = ''
    responses["8PM"] = ''
    responses["9PM"] = ''
    responses["Other"] = ''
#######################################################
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)