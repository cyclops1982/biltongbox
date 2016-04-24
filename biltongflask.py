####################################################################
# Simple script to control temperateu based on heat sensor reading #
####################################################################
from flask import Flask,send_from_directory,render_template, abort
from jinja2 import TemplateNotFound

import os

app = Flask(__name__, template_folder="html")


@app.route('/')
@app.route('/<path:filename>')
def index(filename = None):
		if (filename == None):
			return render_template('index.html')
		else:
			try:
				return render_template(filename)
			except TemplateNotFound:
				abort(404)



@app.route('/css/<path:filename>')
def static_css(filename):
	return send_from_directory(os.path.join(app.root_path, 'html/css/'), filename)

@app.route('/js/<path:filename>')
def static_js(filename):
	return send_from_directory(os.path.join(app.root_path, 'html/js/'), filename)

@app.route('/images/<path:filename>')
def static_images(filename):
	return send_from_directory(os.path.join(app.root_path, 'html/images/'), filename)





if __name__ == "__main__":
	app.debug = True
	app.run(host = '0.0.0.0')
