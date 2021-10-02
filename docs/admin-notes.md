Admin Notes
===========

These notes are intended for admins of this app. They will not work if you don't have access to the `uchicago-cs` team on Heroku.

Setting up a local repo with heroku access
------------------------------------------

Install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

    git clone $REPO_URL
    heroku login
    heroku git:remote -a cs121-officehours-staging -r heroku
    
You can also add a remote for pushing directly to production, but doing so is unwise:
    
    heroku git:remote -a cs121-officehours -r production

Deploying to staging
--------------------

    git push heroku master
    
Applying migrations
-------------------

    heroku run python3 manage.py migrate
    
Running a script
----------------

Make sure you're running the script from the root of the app:

    heroku run "python3 scripts/SCRIPT"
    
To run the script in production:

    heroku run --app cs121-officehours "python3 scripts/SCRIPT"

    
Creating slots
--------------

    python3 scripts/create-slots.py --date 2020-10-04 --start-time 10:00 --end-time 11:00 --slot-minutes 15
    
This will do a dry run. Use the `-u` to actually create the slots.