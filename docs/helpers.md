# Cmnsdjango Helpers

## helpers/update.sh
Update.sh is a shell script that handles updating the django project on the remote host.
It makes a git pull and based on the git output, takes the following actions
- Enable virtual env
- Installs requirements via pip
- Executes pending migrations
- Executes collectstatic
- Restarts the supervisorctl pool name 

In order for the supervisorctl restart, it will check the current directory and use the
first segment of the directory name to restart the pool. So for example, the directory
camping.cmns.nl will trigger a restart of the pool camping.

### Issues with Update.sh
Update.sh has a current issue where the submodule static or migrations changes do not
trigger an update. This is being resolved by experimenting with update.py. 
