import logging
import random
import urllib
import webapp2

from pygments import highlight
from pygments.formatters import HtmlFormatter
import pygments.lexers

import cloudstorage as gcs
from google.appengine.api.app_identity import get_default_gcs_bucket_name
from google.appengine.ext import blobstore, db
from google.appengine.ext.webapp import blobstore_handlers

URL = 'http://sprunge.us'
POST = 'sprunge'

def new_id():
    nid = ''
    symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    while len(nid) < 4:
        n = random.randint(0, 35)
        nid = nid + symbols[n:n + 1]
    return nid

def help():
    form = (
        'data:text/html,<form action="{0}" method="POST">'
        '<textarea name="{1}" cols="80" rows="24"></textarea>'
        '<br><button type="submit">{1}</button></form>'.format(URL, POST)
    )
    return """
<style> a {{ text-decoration: none }} </style>
<pre>
sprunge(1)                          SPRUNGE                          sprunge(1)

NAME
    sprunge: command line pastebin.

SYNOPSIS
    &lt;command&gt; | curl -F '{0}=&lt;-' {1}

DESCRIPTION
    add <a href='{3}'>?&lt;lang&gt;</a> to resulting url for line numbers and syntax highlighting
    use <a href='{2}'>this form</a> to paste from a browser

EXAMPLES
    ~$ cat bin/ching | curl -F '{0}=&lt;-' {1}
       {1}/aXZI
    ~$ firefox {1}/aXZI?py#n-7

SEE ALSO
    http://github.com/rupa/sprunge

</pre>""".format(POST, URL, form, '<a href="http://pygments.org/docs/lexers/"')

def make_blob(nid, data):
    filename = '/{0}/{1}'.format(get_default_gcs_bucket_name(), nid)
    with gcs.open(
        filename, 'w', content_type='text/plain; charset=UTF-8'
    ) as fh:
        fh.write(data.encode('utf-8'))
    blobstore_filename = '/gs{0}'.format(filename)
    return blobstore.create_gs_key(blobstore_filename)

class Sprunge(db.Model):
    name = db.StringProperty()
    content = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    blob = db.StringProperty()

class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.out.write('''
        <html>
        <body>
        {0}
        </body>
        </html>
        '''.format(help()))

    def post(self):
        nid = new_id()
        while Sprunge.gql('WHERE name = :1', nid).get():
            nid = new_id()
        s = Sprunge()
        s.name = nid
        key = make_blob(nid, self.request.get(POST))
        s.blob = key
        try:
            s.put()
        except Exception as ex:
            self.response.out.write('{0}\n'.format(ex))
            logging.error(ex)
            return
        self.response.out.write('{0}/{1}\n'.format(URL, nid))

class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):

    def get(self, resource):
        resource = str(urllib.unquote(resource))

        c = Sprunge.gql('WHERE name = :1', resource).get()
        if not c:
            self.response.out.write('{0} not found.'.format(resource))
            return

        # See if we need to migrate to Blobstore.
        try:
            data = c.blob
        except AttributeError:
            data = c.content
        else:
            if c.blob:
                data = blobstore.BlobReader(c.blob).read()
            else:
                data = c.content
                # migrate
                logging.info(
                    'Migrating {0} from Datastore to Blobstore.'
                    .format(resource)
                )
                key = make_blob(resource, data)
                c.blob = key
                c.content = ''
                try:
                    c.put()
                except Exception as ex:
                    logging.error(ex)

        syntax = self.request.query_string
        if not syntax:
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            self.response.out.write(data + '\n')
            return

        try:
            lexer = pygments.lexers.get_lexer_by_name(syntax)
        except:
            lexer = pygments.lexers.TextLexer()
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.out.write(highlight(
            data,
            lexer,
            HtmlFormatter(
                full=True,
                style='borland',
                lineanchors='n',
                linenos='inline',
                encoding='latin-1' # weird, but this works and utf-8 does not.
            )
        ))

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/([^/]+)?', ServeHandler)],
    debug=False,
)
