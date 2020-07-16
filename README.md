mod-app
=======

This is a work-in-progress desktop application of the MOD interface and backend,
natively integrated in the OS (no external web browser needed).

It requires `mod-host` and `mod-ui`, which you can either have installed system-wide or as part of the git submodules of this repository.

Under Debian-based Linux distrbutions, you can run this to install all the dependencies:

```
sudo apt-get install jack-capture sndfile-tools liblilv-dev
sudo apt-get install python3-pyqt5 python3-pyqt5.qtsvg python3-pyqt5.qtwebkit pyqt5-dev-tools
sudo apt-get install python3-pil python3-pystache python3-serial python3-tornado
```

After you're done installing the dependencies, simply type:

```
make
```

To generate the necessary resource files to be able to run mod-app (and mod-remote).  
If you have git submodules enabled, it will also build `mod-host` and `mod-ui`.

You can now run mod-app using:

```
make run
```

Binary builds will be available at a later date.


mod-remote
==========

This is a work-in-progress application that allows you to connect to a remote MOD device.  
The only required dependency for it is PyQt.
