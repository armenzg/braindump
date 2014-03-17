#!/usr/bin/env python
import argparse
import datetime
import re
from bugzilla.agents import BMOAgent
from operator import attrgetter

dep_tracker = {}
no_deps = []
deps_open = []
deps_resolved = []
unknown = []

html_file='/var/www/html/builds/slave_health/buildduty_report.html'
username = ''
password = ''

# Set whatever REST API options we want
options = {
    'product':          'Release Engineering',
    'component':        'Buildduty',
    'summary':          'problem tracking',
    'summary_type':     'contains',
    'status':           ['UNCONFIRMED','NEW','ASSIGNED','REOPENED'],
    'include_fields':   '_default,attachments,depends_on',
}

loan_request_options = {
    'product':          'Release Engineering',
    'component':        'Loan Requests',
    'email1':           'nobody@mozilla.org',
    'email1_assigned_to': 1,
    'status':           ['UNCONFIRMED','NEW','ASSIGNED','REOPENED'],
}

def generateHTMLHeader():
    now = datetime.datetime.now()
    now_day = now.strftime("%B %d, %Y")
    now_precise = now.strftime("%c")
    header = """<!DOCTYPE html>
 <html>
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Buildduty Report - %s</title>
    <link rel="stylesheet" media="screen,projection,tv" href="https://www.mozilla.org/media/css/responsive-min.css?build=b6689b7" />
    <link rel="stylesheet" href="./jquery.tablesorter/themes/blue/style.css" type="text/css" media="print, projection, screen" />
    <link rel="stylesheet" href="./css/slave_health.css" type="text/css" media="print, projection, screen" />
    <script type="text/javascript" src="./jquery.tablesorter/jquery-1.6.4.min.js"></script>
    <script type="text/javascript" src="./jquery.tablesorter/jquery.tablesorter.js"></script>
    <script language="javaScript" type="text/javascript" src="./js/bugzilla.js"></script>
    <script language="javaScript" type="text/javascript" src="./js/slave_health.js"></script>
  </head>

  <body class="noscript">
    <div id="topbar">
      <div id="title" class="dropdown"><a href="./index.html">Slave Health</a></div>
      <div class="dropdown separator"> &gt; </div>
      <div id="builddutyreport" class="dropdown">Buildduty Report</div>
      <div class="topbarright">
        <div id="generated" class="dropdown">
          Data generated at: <span id="generated">%s</span>
        </div>
      </div>
    </div>

    <div class="container">
""" % (now_day, now_precise)
    return header

def generateInPageLinks(page_sections):
    links = " | ".join("<a href=\"#%s\">%s</a>" % (page_section['name'],
                                                   page_section['title']) for page_section in page_sections)
    return links

def generateBugTable(table_id, title, bugs, css_class=None, strike_deps=False, links=""):
    if not css_class:
        css_class="tablesorter"
    table = "<table id=\"{0}\" class=\"{1}\">\n".format(table_id, css_class)
    table += "<thead><tr><th>Bug&nbsp;ID</th><th>Summary</th><th>Last Updated</th><th>Depends On</th></tr></thead>\n"

    for bug in sorted(bugs, key=attrgetter('last_change_time'), reverse=False):
        summary = re.sub(r'(.*) (problem tracking)', r'<a target="_\1_slave_health" href="slave.html?name=\1">\1</a> \2', bug.summary)
        table += "<tr><td><a href=\"https://bugzil.la/{0}\">Bug&nbsp;{0}</a></td><td>{1}</td><td>{2}</td>\n".format(bug.id, summary, bug.last_change_time)
        table += "<td>"
        if not bug.depends_on:
            table += "None"
        else:
            for dep_bug in bug.depends_on:
                strike_open = ''
                strike_close = ''
                if dep_bug in dep_tracker and dep_tracker[dep_bug] in ['RESOLVED', 'VERIFIED']:
                    strike_open = '<s>'
                    strike_close = '</s>'
                table += "{0}<a href=\"https://bugzil.la/{1}\">{1}</a>{2}, ".format(strike_open, dep_bug, strike_close)
            table = table[:-2]
        table += "</td>\n</tr>\n"
    table += "</table>\n\n"
    table_header = "<strong>%s</strong> <a name =\"%s\" target=\"builddutybugzilla\" href=\"https://bugzilla.mozilla.org/buglist.cgi?bug_id=%s\"><img class=\"bugzilla\" src=\"icons/bugzilla.png\" alt=\"View list in Bugzilla\" title=\"View list in Bugzilla\" /></a>" % \
        (title, table_id, ','.join(str(bug.id) for bug in bugs))
    if links != "":
        table_header += " | <small>%s</small>" % links
    table_header += "\n"

    return table_header + table

def generateHTMLFooter():
    footer = """
<script type="text/javascript">
$(document).ready(function(){
// Don't try to instantiate the sorter if the table is empty
if ($("#nodeps") > 1) {
    $("#nodeps").tablesorter({sortList:[[2,1]], widgets: ["zebra"]});
}
if ($("#depsresolved") > 1) {
    $("#depsresolved").tablesorter({sortList:[[2,1]], widgets: ["zebra"]});
}
if ($("#depsopen") > 1) {
    $("#depsopen").tablesorter({sortList:[[2,1]], widgets: ["zebra"]});
}
if ($("#loanreqs") > 1) {
    $("#loanreqs").tablesorter({sortList:[[2,1]], widgets: ["zebra"]});
}
});
</script>

    </div>

  </body>
</html>
"""
    return footer

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    # Load our agent for BMO
    bmo = BMOAgent(username, password)

    # Get the bugs from the api
    bug_list = bmo.get_bug_list(options)

    for bug in bug_list:
        if not bug.depends_on:
            no_deps.append(bug)
            continue
        found_open_deps = False
        for dep_bug in bug.depends_on:
            if not dep_bug in dep_tracker:
                current_bug = bmo.get_bug(dep_bug)
                if current_bug:
                    try:
                        dep_tracker[dep_bug] = current_bug.status
                    except:
                        # Something has gone wrong with the lookup (bug is confidential?)
                        # so assume it's still open.
                        deps_open.append(bug)
                        found_open_deps = True
                        break
            if not dep_bug in dep_tracker or \
               dep_tracker[dep_bug] not in ['RESOLVED', 'VERIFIED']:
                # We only need to find one dep still open
                deps_open.append(bug)
                found_open_deps = True
                break
        if not found_open_deps:
            deps_resolved.append(bug)

    loan_requests = bmo.get_bug_list(loan_request_options)

    f = open(html_file, 'w')
    f.write(generateHTMLHeader())

    no_deps_desc = {'name': 'nodeps',
                    'title': 'No dependencies (likely new bugs)'}
    deps_resolved_desc = {'name': 'depsresolved',
                          'title': 'All dependencies resolved'}
    deps_open_desc = {'name': 'depsopen',
                      'title': 'Open dependencies'}
    loan_requests_desc = {'name': 'loanreqs',
                          'title': 'Loan requests (new)'}

    f.write(generateBugTable('nodeps',
                             'No dependencies (likely new bugs)',
                             no_deps,
                             links=generateInPageLinks([deps_resolved_desc,
                                                        deps_open_desc,
                                                        loan_requests_desc])
                             ) + '\n')
    f.write("\n<hr/>\n")
    f.write(generateBugTable('depsresolved',
                             'All dependencies resolved',
                             deps_resolved,
                             strike_deps=True,
                             links=generateInPageLinks([no_deps_desc,
                                                        deps_open_desc,
                                                        loan_requests_desc])
                             ) + '\n')
    f.write("\n<hr/>\n")
    f.write(generateBugTable('depsopen',
                             'Open dependencies',
                             deps_open,
                             strike_deps=True,
                             links=generateInPageLinks([no_deps_desc,
                                                        deps_resolved_desc,
                                                        loan_requests_desc])
                             ) + '\n')
    f.write("\n<hr/>\n")
    f.write(generateBugTable('loanreqs',
                             'Loan requests (new)',
                             loan_requests,
                             strike_deps=True,
                             links=generateInPageLinks([no_deps_desc,
                                                        deps_open_desc,
                                                        deps_resolved_desc])
                             ) + '\n')

    f.write(generateHTMLFooter())
