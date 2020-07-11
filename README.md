mod-app
=======

This is a work-in-progress desktop application of the MOD interface and backend,
natively integrated in the OS (no external web browser needed).

It requires `mod-host` to be installed system-wide.  
Also needs `mod-ui`, but you can get that as part of the git submodules of this repository.

Under Debian-based Linux distrbutions, you can run this to install all dependencies:

```
sudo apt-get install jack-capture sndfile-tools
sudo apt-get install python3-pyqt5 pyqt5-dev-tools
sudo apt-get install python3-pyqt5.qtsvg python3-pyqt5.qtwebkit pyqt5-dev-tools
sudo apt-get install python3-pil python3-pystache python3-serial python3-tornado
```

After you're done installing the dependencies, simply type:

```
make
```

To generate the necessary resource files to be able to run mod-app (and mod-remote).

You can now run mod-app using:

```
./source/mod-app
```

Binary builds will be available at a later date.


mod-remote
==========

This is a work-in-progress application that allows you to connect to a remote MOD device.  
The only required dependency for it is PyQt.
