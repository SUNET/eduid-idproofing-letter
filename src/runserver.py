from idproofing_letter import app
import urllib

# Config debug
#print "Config:"
#for key, value in app.config.items():
#    print key, value
#print "end config"

# Endpoint debug
output = []
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods)
    line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, rule))
    output.append(line)

for line in sorted(output):
    print(line)

app.run(debug=app.config['DEBUG'])


