from jinja2 import Markup


class momentjs(object):
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, render_format):
        markup_format = '<script>\ndocument.write(moment("{}").{});\n</script>'
        time_format = '%Y-%m-%dT%H:%M:%S Z'

        return Markup(markup_format.format(time_format, render_format))

    def format(self, fmt):
        return self.render('format("%s")'.format(fmt))

    def calendar(self):
        return self.render('calendar()')

    def fromNow(self):
        return self.render('fromNow()')
