![BIOS Tool Image](https://github.com/LowellDennis/bt/blob/main/BiosTool.jpg)

### What is this repository for? ###

* A tool for working with HPE Server BIOS source code.
* Current Version is V0.9

### How do I get set up? ###

#### Using Installers (Recommended)

**Windows:**
* Download `BIOSTool-<version>-Setup.exe` from releases
* Run the installer and follow the prompts
* Optionally install the VS Code extension during setup
* The installer will add BT to your PATH automatically

**Linux (Debian/Ubuntu):**
```bash
sudo dpkg -i biostool_<version>_all.deb
sudo apt-get install -f  # Fix any dependencies
```

#### Manual Installation from Source

* To get the source use:
```
    git clone git@github.com:LowellDennis/bt.git
```
* Make sure the directory where the clone is made is in your path
* To run you will also need to have Python installed (at least V2.7, but 3+ is suggested)
    * You can get it [here](https://www.python.org/)

#### Building Installers

See [installers/README.md](installers/README.md) for instructions on building installers for Windows and Linux.

### What does it do? ###

BIOS Tool attempts to simplify HPE Server BIOS development.

* Requires minimal setup
    * Global settings only need to be set once
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
    * FUTURE: Assists in committing changes
* It implements simple CLEAN, and BUILD commands
    * Command output is:
        * Automatically captured into log files
        * Output is scrubbed for ERROR and WARNING messages
            * Only relevant output is shown on the screen
                * Logfiles can be used if more details are needed
* Can even send you a text message when the build completes

### How do I use it? ###
~~~
usage: bt <command> [param1 [param2 [...]]]
  where command is one of:
      attach - Add a BIOS repository to the list of repositories.
       build - Build a BIOS for the current BIOS repository or worktree.
       clean - Clean the current BIOS repository or worktree.
      config - Get or set BIOS tool configuration settings.
      create - Creates a new BIOS worktree and adds it to the list of worktrees.
     destroy - Deletes a BIOS worktree and removes it from the list of worktrees.
      detach - Remove a BIOS repository from the list of repositories.
        init - Initialize the local settings for the current BIOS repository or worktree.
       merge - Merge updates from an upstream location into a local repository or worktree.
        move - Move a BIOS worktree.
        pull - Updates a local repository or worktree with changes from its remote location.
        push - Push updates from a local repository or worktree to its remote location.
      select - Select a BIOS repository from the list of repositories.
      status - Get the status of the current BIOS repository or worktree.
      switch - Switch to a different BIOS repository or worktree.
         top - Change directory to the top of the BIOS repository or worktree.

NOTE: command can be abbreviated as far as it does not conflict with
      another command abbreviation

For detailed help on a particular command use the "bt help <command>"
~~~
### How do I get started? ###

Once you have cloned a BIOS repository using 'git clone'
and have the BIOS tool downloaded somewhere in your path, this is how you use it!

* CD to the directory where the BIOS source code repo was cloned

You are now ready to attach repositories to the BIOS tool
~~~
           bt attach
~~~
* Now you can create BIOS worktrees for your development needs.
~~~
            bt create [/repo <path>] <branch> <worktree> [<commit-ish>]
~~~
*  /repo: Path to the pepository from which to create BIOS worktree
   * (default is currently selected repository)
*  branch: Branch name for new BIOS worktree
*  worktree: Base directory of new BIOS worktree
*  commit-ish: Commit ID, tag, or branch on which the new worktree is to be based
   * (default is HEAD)

The next thing you will need to do is initialize the tool settings for the worktree.
~~~
             cd <worktree>
             bt init <name>
~~~
* name: BIOS platform name for current BIOS worktree
   * This is something like U66, A55, or R13
   * Will attempt to autodetect platform directory, CPU name and CPU vendor
   * It will also initialize alert, release, and warnings to off if not already set

If you want to be notified when a BIOS build is completed.
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
| T-Mobile          | [insert 10-digit number]@tmomail.net                 |
| U.S. Cellular     | [insert 10-digit number]@email.uscc.net              |
| Verizon           | [insert 10-digit number]@vtext.com                   |
| Virgin Mobile     | [insert 10-digit number]@vmobl.com                   |
| Republic Wireless | [insert 10-digital number]@text.republicwireless.com |
|-------------------|------------------------------------------------------|

To see the global and local settings for a BIOS source tree
~~~
            bt config
~~~

One More Thing: For the email/text notification to work
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
        * The name of the subdirectory and the .py file must be the same (case sensitive)
        * Also, the name of the main function in the .py file must be this name (case sensitive)
    * any other files the command may need
        * For example, filter.txt is used by CLEAN and BUILD to filter out false error messages,
        * 'send.ps1' is used by BUILD to send completion alerts. 

### Who do I talk to? ###
 This repo is owned and maintained by [Lowell Dennis](mailto:lowell.dennis@hpe.com?subject="BIOS Tool")

### Version History ###
| Version | Explanation                                                                            |
|---------|----------------------------------------------------------------------------------------|
| V0.9	  | Bug fix release                                                                        |
|         | - Fixed NoFilter outputting "None" repeatedly during clean command timeouts            |
|---------|----------------------------------------------------------------------------------------|
| V0.8	  | GUI improvements                                                                       |
|---------|----------------------------------------------------------------------------------------|
| V0.7	  | Professional installers for Windows and Linux                                          |
|         | - Added Inno Setup installer for Windows with VS Code extension auto-install           |
|         | - Added Debian package for Linux distributions                                         |
|         | - Automated build scripts for both platforms                                           |
|---------|----------------------------------------------------------------------------------------|
| V0.6	  | VS Code extension and ITP debugger support                                             |
|         | - Added VS Code extension with full command support and interactive config UI          |
|         | - Added ITP debugger support with /itp flag                                            |
|         | - Standardized boolean settings                                                        |
|---------|----------------------------------------------------------------------------------------|
| V0.5	  | Build progress improvements                                                            |
|         | - Added build progress bar with module count tracking                                  |
|         | - Dynamic adjustment when actual count exceeds estimate                                |
|         | - Cache actual module counts for accurate subsequent builds                            |
|         | - Fixed worktree detection (top command now works in worktrees)                        |
|         | - Organized GUI and VS Code extension into separate folders                            |
|---------|----------------------------------------------------------------------------------------|
| V0.4	  | Big update                                                                             |
|         | - Revamped help text to be more consistent and informative                             |
|         | - Added use of wakepy to keep from sleeping during long operations                     | 
|         | - Updated send.ps1 to work with new version of Outlook (no COM)                        | 
|         | - Added support for uploading BIOS image after build with iLO and OpenBMC              |
|---------|----------------------------------------------------------------------------------------|
| V0.3	  | Fixed a few minor bugs                                                                 |
|---------|----------------------------------------------------------------------------------------|
| V0.2	  | Release to team                                                                        |
|         | - Fixed worktree commands                                                              |
|         | - Cleaned up help details                                                              |
|---------|----------------------------------------------------------------------------------------|
| V0.1	  | Original Release                                                                       |
|---------|----------------------------------------------------------------------------------------|
