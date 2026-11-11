# Burner state under the login banner; install as /etc/profile.d/econet.sh
[ -t 1 ] && [ -x /root/econet-status ] && /root/econet-status
