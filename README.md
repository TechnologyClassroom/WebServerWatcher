# WebServerWatcher

Keep an eye out for successful web requests.

This project is a work-in-progress (WIP), but it is close enough to working
that it is now worth sharing.

This project is a partial improvement for system administrators and pairs well
with several of my other projects such as
[LogReview](https://github.com/TechnologyClassroom/LogReview) and
[FirewallBlockGen](https://github.com/TechnologyClassroom/firewallblockgen/).

## Trying out WebServerWatcher

WebServiceWatcher is still a work-in-progress so bear with these instructions.
Contributions are welcome.

Clone the repository.

    git clone https://github.com/TechnologyClassroom/webserverwatcher

Change to the directory.

    cd webserverwatcher

Copy the configuration file.

    cp config/webserverwatcher.ini.default config/webserverwatcher.ini

Edit the configuration file to at least point to your web server log file.

Run the program as root. Note: This script is not long. Read the thing before
you run it in production. (I am leaving this note until the software becomes
more polished and battle-tested.)

    sudo python3 webserverwatcher.py

## Background

Concept: A reasonably popular, public-facing web server should have a constant
stream of traffic due to the high volume of bots on the modern web. Of all of
the automated traffic, some bots should be programmed well enough to make
successful web requests several times a second. If your server is reasonably
popular and not returning 2xx codes after a period of a few seconds, I propose
that something is wrong.

There are methods that handle this problem already, but I have not seen any
that handle this problem as fast as this script does. Make an issue if you have
a faster method.

### Method 1: SystemD

When a web server like apache2 crashes, the systemd service can start it back
up again. The SystemD method is slower than the WebServiceWatcher method
because there is a period of time where the web server service is still alive
and failing to return successful requests. The SystemD method usually takes
minutes.

### Method 2: Uptime checks

A recurring service can make the equivalence of `curl` requests to the server
to check on the health of the service. If the requests fail, a restart command
can be sent after a given period of time.

The uptime check method is slower than the WebServiceWatcher method because
even when making requests from the localhost, you have to wait for timeouts and
build a pattern over time. The uptime check method usually takes minutes.

### Method 3: Bash loop

If a sysadmin knows that something is wrong with a server, they can continually
kick it back to life with a hacky bash loop in a `tmux` session like this:

`while true; do systemctl restart apache2; sleep 40; date; done`

This hacky method technically will keep the server somewhat alive until a
proper solution can be found. The downside to this is that there will be some
downtime at least while the service restarts even if the problem has gone away.

The WebServiceWatcher method is more responsive because the load might
externally rise or drop and a manually set time span does not account for what
is actually happening on the server.

## License

GPL-3.0-or-later
