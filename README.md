mod-app
=======

This is a work-in-progress desktop application of the MOD interface and backend,<br/>
natively integrated in the OS (no external web browser needed).<br/>

In order to run this application you need to have ingen and mod-ui installed system-wide.<br/>

If you're using the KXStudio repositories, run this command to install all dependencies:<br/>
`sudo apt-get install ingen mod-ui phantomjs python3-pyqt5, python3-pyqt5.qtwebkit`<br/>

Then simply type:<br/>
`make`<br/>
To generate the necessary resource files to be able to run mod-app (and mod-remote).

Binary builds will be available at a later date.


mod-remote
==========

This is a work-in-progress application that allows you to connect to a remote MOD device.<br/>
The only required dependency for it is PyQt.

Binary builds for Windows and MacOS are available, see the releases section on GitHub.
