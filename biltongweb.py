####################################################################
# Simple script to control temperateu based on heat sensor reading #
####################################################################
import web
import mimetypes
import sys

render = web.template.render('html/')

static_dirs = ('css', 'js', 'images')

urls = (
	'/', 'index',
	'/(css|js|images)/.*', 'static'
)



class static:
	def mime_type(self, filename):
		return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

	def GET(self, static_dir):
		try:
			fullpath = './html'
			fullpath += web.ctx.path
			mimetype = self.mime_type(fullpath)
			web.header('Content-type', mimetype)
			with open(fullpath, 'rb') as readfile:
				return readfile.read() 
		except IOError:
			web.notfound()



class index:
	def GET(self):
		return render.index('test')



if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()
