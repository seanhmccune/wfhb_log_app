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

## app.yaml

This is the file that grants us the ability to talk to GAE. The first line tells GAE which application we<br>
will be developing. The other lines in that first block of code tell GAE the environment in which we plan to<br>
develop. Everything else just tell GAE that we are using Django. It's a pretty simple file that we won't have to <br>
mess with that much

## Github Flow

Check out this link for a super - easy for how github works for use : [supa helpful stuff] (https://guides.github.com/introduction/flow/index.html)

or this: [otha helpful stuff] (https://www.youtube.com/watch?v=oFYyTZwMyAg)

The basic idea is this:<br>
1. Make a new branch<br>
To create a new branch via the command line is supereasy.
```bash
$ git branch [insert new branch name here]
```
2. Do work on that branch<br>
This again, isn't terribly difficult
```bash
$ git checkout [insert branch name here]
```
3. Issue a pull request<br>
So you need to push your code to github
```bash
$ git push origin [insert branch name here]
```
After you do this, go to github.iu.edu and click the green button next to the dropdown box of the branches<br>
This will issue the pull request, remember base is the destination branch and compare is the source branch<br>
4. Discuss the changes<br>
5. Merge it with the master branch
