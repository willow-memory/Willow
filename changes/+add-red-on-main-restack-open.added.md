`red-on-main`, `restack-open`: two jobs a session did by hand. red-on-main
holds a red pull request's failing checks to main's last run, so one red on
main too is said not to be the change's; ci.yml runs it on a red pull
request and writes it into the run's summary. restack-open merges main up
into every open pull request that conflicts with its base, by restack's
rules, and pushes the merge or names the conflict for a person;
restack.yml runs it on every push to main, pushing only with RESTACK_TOKEN
