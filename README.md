mod-app
=======

This is a work-in-progress desktop application of the MOD interface and backend,<br/>
natively integrated in the OS (no external web browser needed).<br/>

In order to run this application you need to have ingen, mod-python and mod-ui installed system-wide.<br/>
(mod-python and mod-ui must be using their python3 variants)<br/>

If you're using the KXStudio repositories, run this command to install all dependencies:<br/>
`sudo apt-get install ingen mod-ui-py3 phantomjs python3-pyqt4 pyqt4-dev-tools`

Binary builds will be available at a later date.


mod-remote
==========

This repository also includes mod-remote, an application that allows you to connect to a remote MOD device.<br/>
The only required dependency for it is PyQt.<br/>
Binary builds for Windows and MacOS are available, see the releases section on GitHub.
