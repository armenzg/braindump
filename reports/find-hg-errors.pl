#!/usr/bin/perl

use warnings;
use strict;

sub get_ymd {
    my @TIME = localtime($_[0]);
    my $D = $TIME[3];
    my $M = $TIME[4] + 1;
    my $Y  = $TIME[5] + 1900;
    my ($DAY, $MON);
    # we need to pad in a 0 if number is less than 10
    # this means we'll need to print them out as strings.
    if ( $D < 10 ){
            $DAY = "0$D";
    }else{
            $DAY = $D;
    }
    
    if ( $M < 10 ){
            $MON = "0$M";
    }else{
            $MON = $M;
    }
    return ($Y, $MON, $DAY);
}

my $output=`mktemp`;
my $user="buildbot_reader";
my $pass="UEhmsJVf7dF5";
my $host="tm-b01-slave01.mozilla.org";
my $db="buildbot";
# yesterday
my ($y,$m,$d) = get_ymd(time() - 24*60*60);
my $mindate = "$y/$m/$d";
($y,$m,$d) = get_ymd(time());
my $maxdate = "$y/$m/$d";
# We use 00:07:00 for the time because the times in the db are UTC
my $query="select CONVERT_TZ(steps.starttime, '+00:00', '-07:00') FROM builds LEFT JOIN (sourcestamps) ON (source_id=sourcestamps.id) LEFT JOIN (builders) ON (builder_id=builders.id) LEFT JOIN (steps) ON (builds.id=build_id) WHERE builders.name LIKE 'try%' AND steps.status='2' AND steps.name like '%hg_update%' AND builds.starttime >= '$mindate 00:07:00' AND builds.starttime <= '$maxdate 00:07:00' ORDER BY steps.starttime;";

my @output = `mysql -u$user -p$pass -h$host -D$db --batch --skip-column-names --execute="$query"`;

my %tally = ();

foreach my $line (@output) {
    chomp($line);
    $line =~ s/.* //;
    my ($hour, $minute);
    ($hour, $minute, undef) = split(/:/, $line, 3);
    my $iminute = int($minute);
    if ($iminute >= 00 && $iminute <= 14) {
        $minute = "00";
    }
    elsif ($iminute >= 15 && $iminute <= 29) {
        $minute = "15";
    }
    elsif ($iminute >= 30 && $iminute <= 44) {
        $minute = "30";
    }
    elsif ($iminute >= 45 && $iminute <= 59) {
        $minute = "45";
    }
    my $key = "$hour:$minute";
    if (exists $tally{"$key"}) {
        $tally{"$key"} += 1;
    }
    else {
        $tally{"$key"} = 1;
    }
}

print "Try Mercurial failures on $mindate\n";
my $key;
foreach $key (sort keys %tally) {
    print "$key: $tally{$key}\n";
}

print "\n\nQuery was: $query";
