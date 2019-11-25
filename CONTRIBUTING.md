# Contributing to Avionics

## Purpose of Standardized Contributions
ISP Avionics has struggled to achieve many goals as of Fall 2019. This repo is an effort to create easily understood, used, and developed code for future tours.

Standardized development allows others to easily use this repo in the future. "Get it working" is a wonderful philosophy when developing something for yourself, or when learning how something works, but contributors to this repo should take the next step of implementing a "Can others get it working?" philosophy.

## Standards

### Learn
This is a learning experience, and contributors are expected to want to step outside their traditional wheelhouses. If you don't know how to tackle a problem, ask someone who does. If your code could be cleaner, ask for design advice. Don't procrastinate because you can't handle a task. Ask someone for help, or rescope your goals to match your group's skillset. This is a for-fun project, so don't stress yourself for not knowing everything right out of the gate.

### Development
* **Most importantly**: Keep the file sizes manageable. If a script is doing 10 different things, split it into 10 smaller scripts and one main script that calls the rest. Keep functions to doing *one* thing.
* Document your code.
    * Make a comment at the top of every file describing what's in it.
    * Make a docstring for every function describing what it does, what its parameters are and their types, and what it returns.
* Name your scripts in a fashion that describes what's in it.
* Don't let a directory look like this:
    * `script.py`
    * `script_v2.py`
    * `script_final.py`
    * `script_FINAL_FINAL.py`
  Just wait until it's not buggy, then push. If there's an issue, make a new commit. The previous versions can still be retrieved from past commits. It's not gone--that's the point of git.
* Ideally, a user should only need to call a handful of functions, if not just a single one, from your capability in order to use it. Requiring users to know the nitty-gritty details of your capability in order to use it is a great way to ensure your feature never flies.

### Issues
Make use of the Issues feature of git! Issues are **not** just for bugs, they're for any development ideas or questions you have about the repo. It allows you to notify others when a bug affects them, allows you to track progress in developing new features, and allows you to create development timelines. When you make an issue:
* Tag it appropriately (make tags if needed).
* Assign someone to it (unless it is tagged "future").
* If multiple things need to be resolved to close the issue, create a checklist in the issue description so progress can be tracked.

### Bug Fixes
If you spot a bug, and can easily fix it,
* Create an issue about the bug and tag it appropriately.
* Fix the bug in a clone of the repo.
* Test to make sure your fix doesn't cause other issues.
* Push the fix to the repo.
* Close the issue.

This might seem tedious, and for tiny bugs this will not be necessary. However, this creates a documentation trail for how functionality of the code has changed, and will allow others to see why you've made the changes you have.

### Forks, Branches, and Pull Requests
* In general, Pull Requests from Forks of the repo will not be accepted. This is to prevent the need to merge two vastly different versions of the repo together. This is not to discourage forking the repo for personal use--please do so.
    * If your fork has features you *really* want to see implemented, branch off the master branch, implement your changes, and make a Pull Request from that branch.
* Branches are an excellent way to make sure broken code never ends up on the master branch. If you're developing a new feature or fixing a tricky bug, make a new branch, and make sure its name begins with the Issue number it is trying to resolve. Make a a Pull Request when your branch is ready to merge.
* Pull Requests should:
    * Have at least one assigned reviewer. They should never be merged until approved by a reviewer who **did not** contribute to the changes made in the Pull Request.
    * Have code that is not far behind the master branch. It's a pain to handle that in the Pull Request process. Sync your branch with the master branch before making a Pull Request.
    
### Releases
Once a version of the repo flies, denote that version of the master branch as a Release! This lets future tours know which versions flew, and allows them to see exactly where issues were and what new features to build.
