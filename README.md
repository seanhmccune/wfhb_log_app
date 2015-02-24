wfhb_log_app
============

This is for the wfhb dev team


## Access 

To get access to our shared gmail account 

Email: wfhbDevTeam@gmail.com<br>
Password: Patience158

Here is the host for the GAE cloud sql instance

host = 173.194.250.218<br>
user = root<br>
password = LittleQueenie242

Note: Make sure to add your ip address to the list of authenticated networks before you try to access the SQL database.

superuser - the same as the email and password

## Django Tutorials

This is a link to the django docs (make sure to look at the docs for version 1.5): [docs] (https://docs.djangoproject.com/en/1.5/)

This is a link on how to integrate django with GAE: [Django and GAE] (http://howto.pui.ch/post/39245389801/tutorial-django-on-appengine-using-google-cloud)

You need to download this to make sure that the phone number field works when you run django locally: [download here](https://github.com/stefanfoulis/django-phonenumber-field)

This is the tutorial on the base template. [Click Here](http://effectivedjango.com/tutorial/static.html)

## GAE

Google app engine tutorial: [tutorial] (http://www.lynda.com/Google-App-Engine-tutorials/Deploying-example-app/144080/159207-4.html?autoplay=true)

## Local development

When working on the app locally, you need to change the database to which you connect

You can find this piece of code in this file: /wfhb_log/wfhb_log/settings.py at line 28

If you do not change the database, then django will throw you errors.

## app.yaml

This is the file that grants us the ability to talk to GAE. The first line tells GAE which application we<br>
will be developing. The other lines in that first block of code tell GAE the environment in which we plan to<br>
develop. Everything else just tell GAE that we are using Django. It's a pretty simple file that we won't have to <br>
mess with that much

## Github Flow

Check out this link for a super - easy for how github works for use : [supa helpful stuff] (https://guides.github.com/introduction/flow/index.html)

or this: [otha helpful stuff] (https://www.youtube.com/watch?v=oFYyTZwMyAg)

The basic idea is this:<br>
* Pull from the master branch 


        $ git pull origin master


* Make a new branch - To create a new branch via the command line is supereasy.


        $ git branch [insert new branch here]


* Do work on that branch - This again, isn't terribly difficult


        $ git checkout [insert branch name here]


* Issue a pull request - So you need to push your code to github


        $ git push origin [insert branch name here]


    After you do this, go to github.iu.edu and click the green button next to the dropdown box of the branches. This will issue the pull request, remember base is the destination branch and compare is the source branch


* Discuss the changes
 
* Merge it with the master branch
<br/>

# common git functions
```bash
$ git init → creates an empty repository in git
$ git status → shows files in the git repository
$ git add → start tracking a file/ put it in the Staging Area
$ git commit -m “description” → add the file to repository with a small message detailing changes
$ git log → log of all changes that were committed to repository
$ git push -u username → push local files to the web repository
$ git reset → unstage files
$ git checkout -- filename → undo to the last commit
$ git branch → creates a new branch for debugging code while keeping an original in tact
$ git checkout branch name → switch branches
$ git branch -d name → delete a branch
$ git push → push everything to the repository
```
