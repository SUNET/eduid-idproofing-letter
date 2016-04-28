from __future__ import absolute_import
from idproofing_letter.app import init_idproofing_letter_app
import urllib


name = 'idproofing_letter'
app = init_idproofing_letter_app(name, {})

if __name__ == '__main__':
    # Config debug
    # print "Config:"
    # for key, value in app.config.items():
    #    print key, value
    # print "end config"

    # Endpoint debug
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, rule))
        output.append(line)

    for line in sorted(output):
        app.logger.debug(line)

    app.logger.info('Starting {} app...'.format(name))
    app.run()


