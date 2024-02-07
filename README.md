![BIOS Tool Icon]

### What is this repository for? ###

* A tool for working with HPE Server BIOS source code.
* Current Version is V0.1

### How do I get set up? ###

* To get the source use:
```
    git clone .../bios-tool.git
```
* Make sure the directory where the clone is made is in your path
* In order to run you will also need to have python installed (at least V2.7)
    * You can get it [here](https://www.python.org/)

### What does it do? ###

BIOS Tool attempts to simplify HPE Server BIOS development.

* Requires minimal setup
    * Global settings only need to be setup once
        * These apply to all BIOS worktrees
    * There are only a few local settings
        * These apply only to the current BIOS worktree
* Makes navigating in the BIOS worktree a bit easier
    * It automatically detects the top of the BIOS worktree
    * FUTURE: Use INF files to help find files and navigate
* It automatically detects git worktrees
* Makes working with version control software a bit easier
    * Filters out extraneous "unversioned" files in status output
    * Allows source code to be updated easily
    * FUTURE: Assists in committing and "pushing" changes upstream
* It implements CLEAN, and BUILD
    * Command output is:
        * Automatically captured into log files
        * Output is scrubbed for ERROR and WARNING messages
            * Only relavant ouput is shown on screen
                * Logfiles can be used if more details are needed
* Can even send you a text message when the build completes

### How do I use it? ###
~~~
usage: bt <command> [param1 [param2 [...]]]
  where command is one of:
      attach - Add a BIOS repository to the global repository list
       build - Build a BIOS for current BIOS worktree
       clean - Clean current BIOS worktree
      config - Get or set BIOS tool configuration settings
      create - Create a new BIOS worktree
     destroy - Delete a BIOS worktree
      detach - Remove a BIOS repository from the global repository list.
        init - Initialize local setting for current BIOS worktree
        move - Moves a BIOS worktree
        pull - Pull updates from an upstream remote repository into a local repository.
        push - Pushes updates from a local repository to the upstream remote repository
      select - Select a BIOS repository or list reposititories in the global repository list
      status - Get VCS status of the current BIOS worktree
      switch - Switch to a different BIOS worktree.
         top - Change directory to the top of the current BIOS worktree

NOTE: command can be abbreviated as afar as it does not conflict with
      another command abbreviation

For detailed help on a particular command use "bt help <command>"
~~~
### How do I get started? ###

Once you have cloned a BIOS repository using 'git clone'
and have the BIOS tool downloaded somewhere in your in your path this is how you use it!
* CD to the directory where the BIOS source code repo was cloned
You are now ready attach repositories to the BIOS tool
~~~
           bt attach
~~~
* Now you can create BIOS worktrees for your development needs.
~~~
            bt create [/repo <repo>] [/commit <commit>] [/branch <branch>] [<path>\]name
~~~
*  repo   Repository from which to create BIOS worktree
          * (default is currently selected repository)
*  commit Commit ID from which to start BIOS worktree
          * (default is HEAD)
*  branch Branch name for new BIOS worktree
          * (default creates BIOS worktree as a detached head)
*  path   Base directory of new BIOS worktree
          * (default is the parent of directory containing repo)
*  name   Name to be given to the BIOS worktree
          * (must be appropriate for a directory name)

The next thing you will need to do is initialize the tool settings for the worktree.
~~~
             cd [<path>\]name
             bt init <platform>
~~~
* platform:   Path to the platform directory
Note: will attempt to autodectect the CPU vendor and CPU type
~~~
If you want to be notified when BIOS build complete.
Do the following
~~~
            bt config email <text-email>
            bt config alert on
~~~
| Carrier           | <text-email> setting                                 |
|-------------------|------------------------------------------------------|
| Alltel            | [insert 10-digit number]@message.alltel.com          |
| AT&T              | [insert 10-digit number]@txt.att.net                 |
| Boost Mobile      | [insert 10-digit number]@myboostmobile.com           |
| Sprint            | [insert 10-digit number]@messaging.sprintpcs.com     |
| T-Mobile          | [insert 10-digit number]@tmomail.net                 |
| U.S. Cellular     | [insert 10-digit number]@email.uscc.net              |
| Verizon           | [insert 10-digit number]@vtext.com                   |
| Virgin Mobile     | [insert 10-digit number]@vmobl.com                   |
| Republic Wireless | [insert 10-digital number]@text.republicwireless.com |

To see the global and local settings for a BIOS source tree
~~~
            bt config
~~~

* One More Thing: For the email/text notification to work
    * Outlook and your command shell have to be run at the same privilege level.
    * If your command shell is run with administrator privileges
        * Outlook will also have to be run with administrator privileges.

### How to extend ###
The BIOS tool is easily extended as it is hierarchical by design.
The main program is 'bt.cmd'

* 'bt.cmd' runs the 'bt.py' python script
* 'bt.py' scans the 'bios-tree' directory for command subdirectories
* A command subdirectory contains:
    * 'terse.txt'    - a terse    description of what the command does
    * 'details.txt'  - a detailed description of what the command does
    * 'needs.vcs'    - (if present) indicates need of vcs services
    * '*command*.py' - the code that carries out the command
        * Note: the name of the subdirectory and the .py file must be the same (case sensitive)
        *       the name of the main function in the .py file must also be this name
    * any other files the command may need
        * For example, filter.txt is used by CLEAN and BUILD to filter out false error messages,
        * 'send.ps1' is used by BUILD to send completion alerts. 

### Who do I talk to? ###
 This repo is owned and maintained by [Lowell Dennis](mailto:lowell.dennis@hpe.com?subject="BIOS Tool")

### Version History ###
| Version | Explanation                                                                            |
|---------|----------------------------------------------------------------------------------------|
| V0.1	  | Original Release                                                                       |
|---------|----------------------------------------------------------------------------------------|
