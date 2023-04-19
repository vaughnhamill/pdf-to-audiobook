import voicerss_tts
from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField, IntegerField, validators
from flask_bootstrap import Bootstrap
import PyPDF2
from werkzeug.utils import secure_filename
import os
import shutil

API_KEY = os.getenv("RSS_API_KEY")
hl_dict = {"Arabic (Egypt)": "ar-eg",
           "Arabic (Saudi Arabia)": "ar-sa",
           "Bulgarian": "bg-bg",
           "Catalan": "ca-es",
           "Chinese (China)": "zh-cn",
           "Chinese (Hong Kong)": "zh-hk",
           "Chinese (Taiwan)": "zh-tw",
           "Croatian": "hr-hr",
           "Czech": "cs-cz",
           "Danish": "da-dk",
           "Dutch (Belgium)": "nl-be",
           "Dutch (Netherlands)": "nl-nl",
           "English (Australia)": "en-au",
           "English (Canada)": "en-ca",
           "English (Great Britain)": "en-gb",
           "English (India)": "en-in",
           "English (Ireland)": "en-ie",
           "English (United States)": "en-us",
           "Finnish": "fi-fi",
           "French (Canada)": "fr-ca",
           "French (France)": "fr-fr",
           "French (Switzerland)": "fr-ch",
           "German (Austria)": "de-at",
           "German (Germany)": "de-de",
           "German (Switzerland)": "de-ch",
           "Greek": "el-gr",
           "Hebrew": "he-il",
           "Hindi": "hi-in",
           "Hungarian": "hu-hu",
           "Indonesian": "id-id",
           "Italian": "it-it",
           "Japanese": "ja-jp",
           "Korean": "ko-kr",
           "Malay": "ms-my",
           "Norwegian": "nb-no",
           "Polish": "pl-pl",
           "Portuguese (Brazil)": "pt-br",
           "Portuguese (Portugal)": "pt-pt",
           "Romanian": "ro-ro",
           "Russian": "ru-ru",
           "Slovak": "sk-sk",
           "Slovenian": "sl-si",
           "Spanish (Mexico)": "es-mx",
           "Spanish (Spain)": "es-es",
           "Swedish": "sv-se",
           "Tamil": "ta-in",
           "Thai": "th-th",
           "Turkish": "tr-tr",
           "Vietnamese": "vi-vn",
           }

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
Bootstrap(app)


# Input form
class InputForm(FlaskForm):
    source = FileField("PDF File", validators=[FileRequired(), FileAllowed(["pdf"], "PDFs only!"),])
    language = SelectField("Language", choices=["Arabic (Egypt)", "Arabic (Saudi Arabia)", "Bulgarian", "Catalan",
                                                "Chinese (China)",
                                                "Chinese (Hong Kong)", "Chinese (Taiwan)", "Croatian", "Czech",
                                                "Danish",
                                                "Dutch (Belgium)", "Dutch (Netherlands)", "English (Australia)",
                                                "English (Canada)",
                                                "English (Great Britain)", "English (India)", "English (Ireland)",
                                                "English (United States)",
                                                "Finnish", "French (Canada)", "French (France)", "French (Switzerland)",
                                                "German (Austria)",
                                                "German (Germany)", "German (Switzerland)", "Greek", "Hebrew", "Hindi",
                                                "Hungarian",
                                                "Indonesian", "Italian", "Japanese", "Korean", "Malay", "Norwegian",
                                                "Polish",
                                                "Portuguese (Brazil)", "Portuguese (Portugal)", "Romanian", "Russian",
                                                "Slovak", "Slovenian",
                                                "Spanish (Mexico)", "Spanish (Spain)", "Swedish", "Tamil", "Thai",
                                                "Turkish", "Vietnamese"],
                           default="English (United States)", validators=[validators.input_required()])
    start_page = IntegerField("Starting page to convert (optional)", validators=[validators.optional()])
    end_page = IntegerField("Last page to convert (optional)", validators=[validators.optional()])
    submit = SubmitField("Submit")


def clear_directories():
    for filename in os.listdir("static/upload/"):
        file_path = os.path.join("static/upload/", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"File cannot be deleted: {e}")


def save_file(form):
    f = form.source.data
    filename = secure_filename(f.filename)
    input_file = "static/upload/" + filename
    f.save(input_file)
    return input_file, filename


def get_text_size(text):
    size_bytes = len(text.encode("utf-8"))
    size_kb = size_bytes * 0.001
    return size_kb


# Home page
@app.route("/", methods=["GET", "POST"])
def home():
    form = InputForm()
    if form.validate_on_submit():
        clear_directories()
        input_file, filename = save_file(form)

        text = ""
        start = form.start_page.data
        end = form.end_page.data

        with open(input_file, "rb") as pdf:
            reader = PyPDF2.PdfReader(pdf)
            if not start and not end:
                for num in range(len(reader.pages)):
                    page = reader.pages[num]
                    text += page.extract_text()
            elif start and not end:
                for num in range(start - 1, len(reader.pages)):
                    page = reader.pages[num]
                    text += page.extract_text()
            elif not start and end:
                for num in range(0, end):
                    page = reader.pages[num]
                    text += page.extract_text()
            else:
                for num in range(start - 1, end):
                    page = reader.pages[num]
                    text += page.extract_text()

        size_kb = get_text_size(text)
        if size_kb <= 100:
            audio = voicerss_tts.speech({
                'key': API_KEY,
                'hl': hl_dict[form.language.data],
                'src': text,
                'c': "mp3",
                'f': '44khz_16bit_stereo',
                'b64': 'true'
            })
            if audio["response"] == "":
                flash("There was an error when trying to process the text to audio. Try choosing ")
                return redirect(url_for("home", form=form))
            elif audio["error"]:
                flash(audio["error"])
                return redirect(url_for("home", form=form))
            else:
                pdf_url = url_for("static", filename=f"upload/{filename}")
                return render_template("audio.html", audio=audio["response"], pdf=pdf_url, text=text)
        else:
            flash("Text from source is larger than 100 KB. Cannot process text to audio.")
            return redirect(url_for("home", form=form))
    return render_template("index.html", form=form)


# Run the application
if __name__ == '__main__':
    app.run(debug=True)
