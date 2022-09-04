# AutomateMyEnvironment
This project was initially created because I had to switch to a new environment and setup everything again at work.
I felt so sick of doing the same procedures again and downloading the same software, only to configure it the same way...

It was at that time I realized I needed to automate this!

# How to install?
Go on a freshly installed windows instance, open cmd as an administrator and type:
```Batch
cd %USERPROFILE%/Desktop && powershell -command irm ertugrulsener.de/automate > main.bat && main.bat
```

# Prerequisites
* The script will only work when ran as an administrator (Invoked by a shell, that ran as administrator beforehand)
* The script only works under windows systems
* The script needs a persistent internet connection
* The **Tamper protection** of the windows defender needs to be disabled manually (It's possible to let the script do it - But it's forbidden by law to do so and
even worse to share the "hack" on github. Atleast in germany.)

All these things will also be checked before the script starts running, so you will notice if any "pre-test" failed.

# Wait, you have your private key uploaded in the repositoy.. Isn't that hella unsafe?
Glad that you asked. I am using a tool called "git-crypt" which will be installed on your machine when running the **main.bat** for the first time.
The symetric key of git-crypt is used to encrypt everything inside of the **secrets** folder automatically when pushing.

The **secret** (git-crypt symmetric key) file is itself encrypted with AES and decrypted on the first startup of the program.

# What does the script do for you?

## 1) Installing software
* Install software by using the windows package manager '**scoop**' into a predefined directory '**C:\Software\apps**'.
* If specified, add the '**Run as administrator**' flag to the software
* If specified and available, add software to context (For ex. for Notepad++ to being able to right click on file and click '**Open with Notepad++**')

## 2) Keeping the installed software updated
* A windows service is registered named 'SoftwareUpdater', it will autostart and check for software updates every hour after start
* The service runs under the SYSTEM user with no special rights

## 3) Configure installed software
* Add '**Compare**' plugin to Notepad++
* Allow seeing invisible files and folders in WinSCP
* Skip EULA checks for JetBrains products
* Set default git configurations like setting '**credential.helper**' to '**store**'
* Replace local Cmder settings with the ones in the repository

## 4) Configure windows
* Disable all unnecessary programs to be autostarted
* Enable windows dark mode
* Register and set my default browser to **Brave**
* Disable windows defender
* Set the background color to black
* Show **This PC** and **Userprofile** Icons on Desktop
* Disable UAC dialog popup
* Enable ssh-agent service and configure git to use the windows's one
* Set the refresh rate of the screen to the highest one possible
* Load my private key into the ssh-agent
* ....
