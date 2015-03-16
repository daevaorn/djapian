# Installing Xapian #

This section covers installation process of Xapian and Xapian bindings 1.0.2 to your machine

## Content ##



## Requirements ##
  * Linux (if you know how to install Xapian in Windows, let me know)
  * wget
  * gcc/g++ (compile only)
  * Python shared (default in Linux, but **not** in Freebsd)

## Install ##

### From packages ###
There are a very good "How to install" packages in Xapian website:
http://xapian.org/download.php

#### For Ubuntu ####
The version required to properly run Djapian (Xapian >=1.0.2) is found in Ubuntu Gutsy and upward :
```
 sudo apt-get install python-xapian xapian-tools
```

### From source ###

#### Xapian Core ####
```
wget http://www.oligarchy.co.uk/xapian/1.0.2/xapian-core-1.0.2.tar.gz
tar -zxvf xapian-core-1.0.2.tar.gz
cd xapian-core-1.0.2
./configure --prefix=/usr/local/xapian-1.0.2
make
su
make install
```

#### Xapian Bindings ####
**Note**: You must install xapian-core before this
```
wget http://www.oligarchy.co.uk/xapian/1.0.2/xapian-bindings-1.0.2.tar.gz
tar -zxvf xapian-bindings-1.0.2.tar.gz
cd xapian-bindings-1.0.2
./configure --with-python
make
su
make install
```

# Installing Djapian #

To install Djapian you'll have to choice on of this available ways:

## 1. Installation using source package ##

You can download [source archive](http://djapian.googlecode.com/files/Djapian-2.0.tar.gz) and unpack it and with root privileges run (or use --prefix option):

```
# python setup.py install
```

## 2. Installation using easy\_install ##

Djapian package can be installed with [setuptools'](http://peak.telecommunity.com/DevCenter/setuptools) `easy_install` program. To do so you need setuptools installed and this shell commands (with root prestigious):

```
# easy_install Djapian
```
or
```
# easy_install http://djapian.googlecode.com/files/Djapian-2.0.tar.gz
```

## 3. Installation of bleeding edge development version (not recommended) ##

For this setup variant you also need Subversion client. To get the most current source you have to checkout our repository:

```
svn checkout http://djapian.googlecode.com/svn/trunk/ djapian
```

Then configure your `PYTHON_PATH` environment variable to include "_/path/to/checkout/parent/dir/_djapian/src"

## Other package sources ##

Djapian can also be obtained from PyPi repository:

http://pypi.python.org/pypi/Djapian