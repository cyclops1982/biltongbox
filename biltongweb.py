####################################################################
# Simple script to control temperateu based on heat sensor reading #
####################################################################
import web


render=web.template.render('html/')

urls = (
	'/', 'index'
)


class index:
	def GET(self):
		i = web.input(name=None)
		return render.index(i.name)



if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()
