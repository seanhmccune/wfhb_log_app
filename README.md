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

superuser - the same as the email and password

## Django Tutorials

This is a link to the django docs (make sure to look at the docs for version 1.5): [docs] (https://docs.djangoproject.com/en/1.5/)

This is a link on how to integrate django with GAE: [Django and GAE] (http://howto.pui.ch/post/39245389801/tutorial-django-on-appengine-using-google-cloud)

## GAE

Google app engine tutorial: [tutorial] (http://www.lynda.com/Google-App-Engine-tutorials/Deploying-example-app/144080/159207-4.html?autoplay=true)

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
