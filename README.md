# pgn2scid
A convenient  GUI wrapper for scmerge and pgnscid with some extra functionality

### What is pgn2scid?

pgn2scid basically is a convenient GUI wrapper (a graphical user interface for command line tools) for 'pgnscid' and 'scmerge', two programs to convert PGN files to native 'Scid' database files and to merge a number of 'Scid' files with an existing 'Scid' database. Both tools should be part of a standard 'Scid vs. PC' installation.

But there's more! In detail pgn2scid can:

* run on multiple platforms

* keep your database up to date automatically by downloading the PGN game collections kindly provided by 'The Week in Chess' (http://theweekinchess.com/).

* keep track of your downloads so that only the latest files which haven’t already been downloaded are selectable.

* process PGN files from other sources, let’s say from your last OTB tournament or games played on a chess server. All you have to do is to put those files in pgn2scid’s working directory.

* automatically uncompress zipped PGN files.

* automatically merge a number of PGN files into one single file.

* convert any number of PGN files to the native 'Scid' database format without the hassle of using command line tools.

* create a zipped backup of an existing 'Scid' database before performing any database merge operations.

* add any number of 'Scid' files to an existing database also without to use a command line tool.

* every step described above is optional.

* store all settings in an initialisation file so pgn2scid is already preconfigured next time it is started.

pgn2scid requires Python 3.4 or newer. For Windows users there's a pre-build executable available so that there's no need to download and install Python first. In this case just download and unzip the file 'pgn2scid_win_executable.zip'. It contains everything you need to run pgn2scid as well as the manual.

### pgn2scid in a Docker container
For Mac users there's now a very convenient way to use pgn2scid. Thanks to Kayvan Sylvan there's a Docker container available which enables you to use pgn2scid without installing Python or any other dependencies, under the condition that your system meets the requirements to run Docker containers. pgn2scid in a container can also be used with Linux. If you are unfamiliar with the concepts of Docker you can get some information on https://www.docker.com/what-docker

If you would like to give it a try please visit

https://github.com/ksylvan/docker-pgn2scid

https://hub.docker.com/r/kayvan/pgn2scid/

Please read the PDF manual for generall information on how to install and use pgn2scid.
