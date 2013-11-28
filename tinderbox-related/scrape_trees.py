#!/usr/bin/python
from BeautifulSoup import BeautifulSoup
import urllib
import os, re

def loadTree(tree):
    url = "http://tinderbox.mozilla.org/admintree.cgi?tree=%s" % tree
    html = urllib.urlopen(url).read()
    massage = [
            (re.compile('"LINK'), lambda match: '" LINK'),
                ]
    return BeautifulSoup(html, markupMassage=massage)

def getInputs(form):
    retval = []
    for i in form.findAll('input'):
        if not i.has_key('name'):
            continue
        name = i['name']
        if i.has_key('type') and i['type'] == 'checkbox':
            if i.has_key('checked'):
                value = '1'
            elif name.startswith("scrape_"):
                print "Setting", name, "to scrape"
                value = '1'
            else:
                continue
        elif i.has_key('type') and i['type'].lower() == 'hidden':
            if i.has_key('checked'):
                value = '1'
            elif i.has_key('value'):
                value = i['value']
            else:
                continue
        elif i.has_key('value'):
            value = i['value']
        else:
            continue
        retval.append((name, value))
    return retval

def saveTree(params):
    return urllib.urlopen("http://tinderbox.mozilla.org/doadmin.cgi", params)

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.set_defaults(
            dry_run=True,
            password=None,
            )
    parser.add_option("--do-it", dest="dry_run", action="store_const", const=False)
    parser.add_option("-p", "--password", dest="password")
    options, trees = parser.parse_args()

    for tree in trees:
        dom = loadTree(tree)
        form = dom.findAll('input', attrs=dict(type="HIDDEN", name="command", value="admin_builds"))[0].parent
        inputs = getInputs(form)

        if not options.dry_run:
            if options.password:
                password = options.password
            else:
                from getpass import getpass
                password = getpass("Tinderbox password:")

            inputs.append(('password', password))

            query_data = urllib.urlencode(inputs)
            retval = saveTree(query_data)
            retval.read()
