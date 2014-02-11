#!/usr/bin/perl -w

use strict;
use Getopt::Long;

sub usage {
    my $user = $ENV{'USER'};
    die <<EOF;
Usage: $0 --username=<username> --master-kind=<build|test> [--master-dir=<master_dir>]

Arguments:

 -u|--username=$user
 -b|--basedir=/builds/buildbot
 -m|--master-dir=build1
 --master-kind=<test|build>
 --http-port=8044
 --dry-run
 -h|--help
EOF
}

sub write_file {
    @_ == 2 or die;
    my ($outfile, $content) = @_;
    open(my $fh, ">", $outfile) or die "Error creating file '$outfile': $!";
    print $fh $content;
    close($fh) or die "Error closing file '$outfile': $!";
}

my $HOME = $ENV{'HOME'};
my $username = $ENV{'USER'};
my $hostname = 'dev-master1.srv.releng.scl3.mozilla.com';
my $basedir = '/builds/buildbot';
my $master_dir;
my $dry_run = 0;
my $master_kind;
my $show_help = 0;
my $http_port = 8044;
my $build_config_json = q'
[{
  "basedir": "BASEDIR/USERNAME/MASTERDIR",
  "bbconfigs_branch": "default",
  "bbconfigs_dir": "BASEDIR/USERNAME/MASTERDIR/buildbot-configs",
  "bbcustom_branch": "default",
  "bbcustom_dir": "BASEDIR/USERNAME/MASTERDIR/buildbotcustom",
  "buildbot_bin": "BASEDIR/USERNAME/MASTERDIR/bin/buildbot",
  "buildbot_branch": "default",
  "buildbot_python": "BASEDIR/USERNAME/MASTERDIR/bin/python",
  "buildbot_setup": "BASEDIR/USERNAME/MASTERDIR/buildbot/master/setup.py",
  "buildbot_version": "0.8.2",
  "datacentre": "scl1",
  "db_name": "HOSTNAME:BASEDIR/USERNAME/MASTERDIR/master",
  "enabled": true,
  "environment": "staging",
  "hostname": "HOSTNAME",
  "http_port": HTTP_PORT,
  "limit_b2g_branches": [],
  "limit_branches": [],
  "limit_projects": [],
  "limit_tb_branches": [],
  "master_dir": "BASEDIR/USERNAME/MASTERDIR/master",
  "mobile_release_branches": [],
  "name": "sm-USERNAME",
  "pb_port": PB_PORT,
  "release_branches": [],
  "role": "build",
  "ssh_port": SSH_PORT,
  "thunderbird_release_branches": [],
  "tools_branch": "default",
  "tools_dir": "BASEDIR/USERNAME/MASTERDIR/tools"
}]
';

my $test_config_json = q'
[{
    "basedir": "BASEDIR/USERNAME/MASTERDIR",
    "bbconfigs_branch": "default",
    "bbconfigs_dir": "BASEDIR/USERNAME/MASTERDIR/buildbot-configs",
    "bbcustom_branch": "default",
    "bbcustom_dir": "BASEDIR/USERNAME/MASTERDIR/buildbotcustom",
    "buildbot_bin": "BASEDIR/USERNAME/MASTERDIR/bin/buildbot",
    "buildbot_branch": "default",
    "buildbot_python": "BASEDIR/USERNAME/MASTERDIR/bin/python",
    "buildbot_setup": "BASEDIR/USERNAME/MASTERDIR/master/setup.py",
    "buildbot_version": "0.8.2",
    "datacentre": "scl1",
    "db_name": "HOSTNAME:BASEDIR/USERNAME/MASTERDIR/master",
    "enabled": true,
    "environment": "staging",
    "hostname": "HOSTNAME",
    "http_port": HTTP_PORT,
    "master_dir": "BASEDIR/USERNAME/MASTERDIR/master",
    "name": "sm-USERNAME",
    "pb_port": PB_PORT,
    "role": "tests",
    "ssh_port": SSH_PORT,
    "tools_branch": "default",
    "tools_dir": "BASEDIR/USERNAME/MASTERDIR/tools"
}]
';

GetOptions('u|username=s' =>   \$username,
           'b|basedir=s'  =>   \$basedir,
           'm|master-dir=s' => \$master_dir,
           'master-kind=s' => \$master_kind,
           'http-port=i' => \$ http_port,
           'dry-run' => \$dry_run,
           'help' => \$show_help,
) or usage();
usage() if $show_help;
usage() unless defined($username);
usage() unless defined($basedir);
usage() unless defined($master_kind) and $master_kind =~ m/^(build|test)$/;

sub run {
    my $cmd = shift || die;
    print("Running '$cmd'\n");
    system($cmd) == 0 or die "Error running '$cmd'\n";
}

sub cd {
    my $dir = shift || die;
    print("chdir $dir\n");
    chdir($dir) or die "Could not chdir '$dir': $!";
}

my $config_json;
if ($master_kind eq "build") {
    $config_json = $build_config_json;
    $master_dir = 'build1' unless defined($master_dir);
}
elsif ($master_kind eq "test") {
    $config_json = $test_config_json;
    $master_dir = 'test1' unless defined($master_dir);
}
else {
    die "Error: Invalid --master-kind '$master_kind'\n";
}

my $pb_port = $http_port + 1000;
my $ssh_port = $http_port - 1000;

$config_json =~ s/BASEDIR/$basedir/g;
$config_json =~ s/USERNAME/$username/g;
$config_json =~ s/MASTERDIR/$master_dir/g;
$config_json =~ s/HTTP_PORT/$http_port/g;
$config_json =~ s/PB_PORT/$pb_port/g;
$config_json =~ s/SSH_PORT/$ssh_port/g;
$config_json =~ s/HOSTNAME/$hostname/g;

my $outdir = "$basedir/$username/$master_dir";

if (-d $outdir) {
    die("Error: Directory '$outdir' already exists. Specify a different master-dir?\n");
}

print("mkdir $outdir\n");
mkdir($outdir) or die("Could not mkdir '$outdir': $!");
print("chdir $outdir\n");
chdir($outdir) or die("Could not chdir '$outdir': $!");
print("writing config.json\n");
write_file("config.json", $config_json);
run("hg -q clone http://hg.mozilla.org/build/buildbot-configs tmp");
cd("tmp");
run("make -f Makefile.setup MASTER_NAME=sm-$username BASEDIR=$outdir PYTHON=python2.6 VIRTUALENV=virtualenv BUILDBOTCUSTOM_BRANCH=default BUILDBOTCONFIGS_BRANCH=default USER=$username MASTERS_JSON=$outdir/config.json virtualenv deps install-buildbot master master-makefile");

cd("$outdir/master");
if (-e "$HOME/passwords.py") {
    run("cp $HOME/passwords.py .");
}
else {
    print("NOTE: You may need to populate master/passwords.py so the download_token step doesn't fail.\n");
}
print("NOTE: Adjust queuedir setting /dev/shm/<yourname> so sendchanges work as expected.\n");

run("rm master.cfg");
if ($master_kind eq 'build') {
    run("ln -s ../buildbot-configs/mozilla/universal_master_sqlite.cfg master.cfg");
}
elsif ($master_kind eq 'test') {
    run("ln -s ../buildbot-configs/mozilla-tests/universal_master_sqlite.cfg master.cfg");
}

print("NOTE: Add branches of interest to master/master_config.json limit_branches, release_branches, etc.\n");
