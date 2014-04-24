#!/bin/sh -ex

FROM_URL="https://hg.mozilla.org/gaia-l10n"
TO_URL="ssh://hg.mozilla.org/releases/gaia-l10n/v1_4/"

LOCALES="ar
as
ast
be
bg
bn-BD
bn-IN
bs
ca
cs
cy
da
de
el
en-GB
en-US
eo
es
et
eu
fa
ff
fr
fy-NL
ga-IE
gd
gl
gu
he
hi-IN
hr
ht
hu
id
it
ja
km
kn
ko
lij
lt
mk
ml
mr
ms
nb-NO
ne-NP
nl
or
pa
pl
pt-BR
ro
ru
si
sk
sl
sq
sr-Cyrl
sr-Latn
sv-SE
ta
te
th
tr
ur
vi
xh
zh-CN
zh-TW"

for l in $LOCALES; do
    echo $FROM_URL/$l to $TO_URL/$l
    if [ ! -e $l ] ; then
        hg clone $FROM_URL/$l
    else
        hg --cwd $l pull -u
    fi
    hg --cwd $l push $TO_URL/$l
done
