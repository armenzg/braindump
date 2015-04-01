#! /bin/bash
#
# This is a helper script to read in most of the top-level mozconfigs in
# mozilla-central, and dump out the settings of the MOZ_AUTOMATION variables.
# The output is a '1' or '0' if the MOZ_AUTOMATION variable is explicitly set
# to either 1 or 0, or '.' if the default value from build/mozconfig.automation
# will be used. A '@' character at the end of the mozconfig path indicates that
# it is parsed using IS_NIGHTLY=yes, whereas a mozconfig with 'nightly' in the
# path but no '@' character has no IS_NIGHTLY setting, and is usually used for
# opt builds.
#
# Usage:
#  1) (on Linux/OSX): comment out all of build/mozconfig.vs-common, or else
#     you'll see this when parsing Windows configs:
#     build/mozconfig.vs-common: line 2: syntax error near unexpected token `$'{\r''
#     build/mozconfig.vs-common: line 2: `mk_export_correct_style() {
#
#  2) cd /path/to/mozilla-central; bash /path/to/dump-mozconfigs.bash
#
#  You'll want a wide terminal to see all the output.

ac_add_options()
{
	true
}

mk_add_options()
{
	true
}

mk_export_correct_style()
{
	true
}

ac_add_app_options()
{
	true
}

parse_config()
{
	config=$1
	is_nightly=$2
	(
	if [ "$is_nightly" != "" ]; then
		export IS_NIGHTLY="yes"
	fi
	. ./$config
	text=$config$is_nightly
	echo -n "$text:"
	echo -n "$text:" | wc -c | awk 'BEGIN{ORS=""} {x=$1/8; for(y=x;y<8;y++) {print "	"}}'
	for i in BUILD_SYMBOLS L10N_CHECK PACKAGE PACKAGE_TESTS INSTALLER UPDATE_PACKAGING UPLOAD UPLOAD_SYMBOLS SDK; do
		varname=MOZ_AUTOMATION_$i
		prettyvarname=MOZ_AUTOMATION_PRETTY_$i
		prettyvar=""
		if [ "${!prettyvarname}x" == "1x" ]; then
			prettyvar="P"
		fi
		echo -n "${!varname-.}$prettyvar	"
	done
	)
	echo ""
}

topsrcdir=`pwd`
mozconfigs="b2g/config/mozconfigs/linux32_gecko/debug
b2g/config/mozconfigs/linux32_gecko/nightly
b2g/config/mozconfigs/linux64_gecko/debug
b2g/config/mozconfigs/linux64_gecko/nightly
b2g/config/mozconfigs/macosx64_gecko/debug
b2g/config/mozconfigs/macosx64_gecko/nightly
b2g/config/mozconfigs/win32_gecko/debug
b2g/config/mozconfigs/win32_gecko/nightly
b2g/dev/config/mozconfigs/linux64/mulet
b2g/dev/config/mozconfigs/macosx64/mulet
b2g/dev/config/mozconfigs/win32/mulet
browser/config/mozconfigs/linux32/debug
browser/config/mozconfigs/linux32/nightly
browser/config/mozconfigs/linux64/code-coverage
browser/config/mozconfigs/linux64/debug
browser/config/mozconfigs/linux64/debug-asan
browser/config/mozconfigs/linux64/debug-static-analysis-clang
browser/config/mozconfigs/linux64/nightly
browser/config/mozconfigs/linux64/nightly-asan
browser/config/mozconfigs/macosx64/debug
browser/config/mozconfigs/macosx64/debug-static-analysis
browser/config/mozconfigs/macosx-universal/nightly
browser/config/mozconfigs/win32/debug
browser/config/mozconfigs/win32/nightly
browser/config/mozconfigs/win64/debug
browser/config/mozconfigs/win64/nightly"

echo "								bldsyms	l10nchk	pkg	pkgtst	install	mar	upload	upsyms	sdk"
for j in $mozconfigs; do
	parse_config $j
	if echo $j | grep '\(nightly\|mulet\)' > /dev/null; then
		parse_config $j @
	fi
done
