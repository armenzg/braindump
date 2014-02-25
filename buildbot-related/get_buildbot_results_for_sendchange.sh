#!/bin/bash -e

### DEFAULTS ###
max_records=100
master_url='http://dev-master1.srv.releng.scl3.mozilla.com:8036'
user='kmoir'
host='dev-master1'
remote_dir='/builds/buildbot/kmoir/test2'

function usage {
    echo
    echo "get_buildbot_results_for_sendchange.sh -h                   Displays this help message"
    echo
    echo "get_buildbot_results_for_sendchange.sh -u USERNAME          Looks for all Builders associated to the given USERNAME specified"
    echo "                                       [ -m MASTER_URL ]    in the sendchanges(s) that triggered the Builders. MAX_RECORDS is"
    echo "                                       [ -l USER ]          an optional parameter that says how many records to iterate"
    echo "                                       [ -s HOST ]          through, when parsing the buildbot web interface, starting from"
    echo "                                       [ -r REMOTE_DIR ]    the most recent Builder, to find all the Builders. The other"
    echo "                                       [ -x MAX_RECORDS ]   optional parameters relate to which buildmaster to use. Defaults,"
    echo "                                                            if not specified on the command line, are:"
    echo "                                                                 MASTER_URL='${master_url}'"
    echo "                                                                 USER='${user}'"
    echo "                                                                 HOST='${host}'"
    echo "                                                                 REMOTE_DIR='${remote_dir}'"
    echo "                                                                 MAX_RECORDS='${max_records}'"
    echo
    echo "This script allows you to pull back the Builders that run as a result of your sendchange(s). It enables you to filter the"
    echo "results from the buildmaster you specify, so that only Builders related to your particular sendchange(s) are shown, otherwise"
    echo "it is difficult to know at a glance which ones relate to your sendchange, and which are from other unrelated sendchanges."
    echo
    echo "Two independent mechanisms are used, which should give identical results. Both sets of results are shown, together with any"
    echo "differences between them, to aid troubleshooting. The two mechanisms are:"
    echo "    1) Parsing the buildbot web interface, to find builders related to the specified sendchange(s)"
    echo "    2) Querying the sqlite3 database that is used by buildbot, to get results directly from the database"
    echo
}

while getopts ':hu:x:m:l:s:r:' OPT
do
    case "${OPT}" in
        h) usage
           exit 0;;
        u) username="${OPTARG}";;
        x) max_records="${OPTARG}";;
        m) master_url="${OPTARG}";;
        l) user="${OPTARG}";;
        s) host="${OPTARG}";;
        r) remote_dir="${OPTARG}";;
        *) echo >&2
           echo "Invalid option specified" >&2
           usage >&2
           exit 64;;
    esac
done

if [ -z "${username}" ]
then
    usage >&2
    exit 64
fi

# find urls from web interface
web_builder_urls="$(mktemp -t web.XXXXXXXXXX)"

page_cache="$(mktemp -t page_cache.XXXXXXXXXX)"
# iterate through recent_builds page (100 most recent builds), and pull out only ones with correct sendchange author
curl "${master_url}/one_line_per_build?numbuilds=${max_records}" 2>/dev/null | sed -n 's/.*<a href="\([^"]*\)">#[0-9][0-9]*<\/a>.*/'"${master_url//\//\\/}"'\/\1/p' | while read url
do
    curl "${url}" 2>/dev/null > "${page_cache}"
    if grep -Fq "${username}" "${page_cache}"
    then
        result="$(sed -n -e 's/.*class="\([a-z]*\) result".*/\1/p' "${page_cache}" | head -1)"
        case "${result}" in
            success)   echo "${url}|0";;
            warnings)  echo "${url}|1";;
            failure)   echo "${url}|2";;
            skipped)   echo "${url}|3";;
            exception) echo "${url}|4";;
            retry)     echo "${url}|5";;
            cancelled) echo "${url}|6";;
            *)         echo "${url}|?";;
        esac
    fi
done | sort -u > "${web_builder_urls}"

# now query database directly, to see if we get same results, applying same constraint to username
sqlite3_builder_urls="$(mktemp -t sqlite3.XXXXXXXXXX)"

ssh "${user}@${host}" "sqlite3 '${remote_dir}/master/state.sqlite'"' "select
    '\'"${master_url}/builders/"\'' || br.buildername || '\''/builds/'\'' || b.number as url, br.results
from
  buildrequests br,
  builds b,
  buildsets bs,
  sourcestamp_changes ssc,
  changes c
where
  c.author like '\'"${username}%"\''
  and ssc.changeid = c.changeid
  and bs.sourcestampid = ssc.sourcestampid
  and br.buildsetid = bs.id
  and b.brid=br.id
  and br.complete = 1
  and br.results is not null"' | sed 's/ /%20/g' | sort -u > "${sqlite3_builder_urls}"

# now fix results to have RETRY result if they were retried...

cat "${sqlite3_builder_urls}" | sed 's/\/[^/]*$//' | sort -u | while read urlprefix
do
    cat "${sqlite3_builder_urls}" | grep -F "${urlprefix}" | sed '$d' | while read line
    do
        cat "${sqlite3_builder_urls}" | sed "s/^\(${line//\//\\/}.*\)|[0-6]$/\1|5/" > "${sqlite3_builder_urls}."
        mv "${sqlite3_builder_urls}." "${sqlite3_builder_urls}"
    done
done


echo "Web interface results:"
echo "======================"
cat "${web_builder_urls}"
echo
echo "Database results:"
echo "================="
cat "${sqlite3_builder_urls}"
echo
echo "Differences overview"
echo "===================="
echo
echo "<: indicates it is in the web interface only"
echo ">: indicates it is found in the database only"
echo
diff "${web_builder_urls}" "${sqlite3_builder_urls}" | grep '^<\|>' | sort
rm "${web_builder_urls}" "${sqlite3_builder_urls}" "${page_cache}"
