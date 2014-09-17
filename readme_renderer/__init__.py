from genshi.filters import Transformer
from genshi.builder import tag
from genshi.core import Markup, Stream
from trac.core import *
#from trac.config import Option, IntOption
from trac.mimeview.api import Mimeview, IHTMLPreviewRenderer, content_to_unicode, is_binary
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from trac.util.text import to_unicode

class ReadmeRendererPlugin(Component):
	implements(ITemplateStreamFilter, ITemplateProvider, IHTMLPreviewRenderer)

	# http://tools.ietf.org/html/draft-ietf-appsawg-text-markdown-01
	# http://tools.ietf.org/html/draft-seantek-text-markdown-media-type-00
	#returns_source = True
	def get_quality_ratio(self, mimetype):
		if mimetype in ('text/markdown', 'text/x-markdown', 'text/x-web-markdown', 'text/vnd.daringfireball.markdown'):
			return 8
		return 0

	def render(self, context, mimetype, content, filename=None, url=None):
		self.log.debug("Using Markdown Mimeviewer")
		req = context.req
		add_stylesheet(req, 'readme/readme.css')
		add_script(req, 'readme/marked.js')
		content = content_to_unicode(self.env, content, mimetype)
		# for some insane reason genshi will only preserve whitespace of <pre> elements, trac calls Stream.render() inappropriately.
		return tag.pre(content.encode('utf-8'))

	def filter_stream(self, req, method, template, stream, data):
		if not (template == 'browser.html' and data.get('dir')):
			if ((not data.get('dir')) and (data.get('path')) and (data.get('path').endswith('.md'))):	# Rendering single markdown file preview
				stream = stream | Transformer("//head/script[not(@src)][1]").after(
					tag.script(
						Markup(
							"jQuery(document).ready(function($) {"
							"  $('#preview').each(function() {"
							"    $(this).html(marked( $(this).children('pre').first().text() ));"
							"  });"
							"});"
						),
						type = "text/javascript"
					)
				)
			return stream

		add_stylesheet(req, 'common/css/code.css')

		repos = data.get('repos') or self.env.get_repository()
		rev = req.args.get('rev', None)

		for entry in data['dir']['entries']:						# Rendering all READMEs in a directory preview
			try:
				if not entry.isdir and entry.name.lower().startswith('readme'):
					node = repos.get_node(entry.path, rev)
					req.perm(data['context'].resource).require('FILE_VIEW')
					mimeview = Mimeview(self.env)
					content = node.get_content()
					mimetype = node.content_type
					divclass = 'searchable'
					if entry.name.lower().endswith('.wiki'):
						mimetype = 'text/x-trac-wiki'
						divclass = 'searchable wiki'
					elif entry.name.lower().endswith('.md'):
						mimetype = 'text/x-markdown'
						divclass = 'searchable markdown'
					if not mimetype or mimetype == 'application/octet-stream':
						mimetype = mimeview.get_mimetype(node.name, content.read(4096)) or mimetype or 'text/plain'
					del content
					self.log.debug("ReadmeRenderer: rendering node %s@%s as %s" % (node.name, str(rev), mimetype))
					output = mimeview.preview_data(
						data['context'],
						node.get_content(),
						node.get_content_length(),
						mimetype,
						node.created_path,
						'',
						annotations = [],
						force_source = False
					)

					if output:
						if isinstance(output['rendered'], Stream):
							#content = output['rendered'].select('./pre/node()')
							#content = output['rendered'].select('./pre')
							content = output['rendered'].select('.')
						else:
							self.log.debug("GOT THERE")
							content = output['rendered']
						insert = tag.div(
							tag.h1(entry.name,
								tag.a(Markup(' &para;'),
									class_ = "anchor",
									href   = '#' + entry.name,
									title  = 'Link to file'
								),
								id_ = entry.name
							),
							tag.div(
								content,
								#xml:space = "preserve",
								class_ = divclass,
								title = entry.name
							),
							class_ = "readme",
							style  = "padding-top: 1em;"
						)
						stream = stream | Transformer("//div[@id='content']/div[@id='help']").before(insert)
			except Exception, e:
				self.log.debug(to_unicode(e))
		stream = stream | Transformer("//head/script[not(@src)][1]").after(
			tag.script(
				Markup(
					"jQuery(document).ready(function($) {"
					"  $('.markdown').each(function() {"
					"    $(this).html(marked( $(this).children('pre').first().html() ));"
					"  });"
					"});"
				),
				type = "text/javascript"
			)
		)
		return stream

	def get_templates_dirs(self):
		from pkg_resources import resource_filename
		return [resource_filename(__name__, 'htdocs')]

	def get_htdocs_dirs(self):
		from pkg_resources import resource_filename
		return [('readme', resource_filename(__name__, 'htdocs'))]
