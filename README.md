DynalabExt
==========


`DynalabExt` is a tentative custom [Inkscape](https://inkscape.org/) extension
for use at the [Dynalab](https://fablab.chambery.fr/) Fablab, in Chambéry,
France.



Installation
------------


 1. Get the path to Inkscape's user extensions directory: from a running
    inkscape, go to the menu `Edit => Preferences => System => User extensions`

 2. create the folder `Dynalab` into Inkscape's user extensions directory (from
    previous point), or empty it if it already exists

 3. copy the `Dynalab/src/` directory AND one of the `Dynalab/menu-??/`
    directory to the `Dynalab` directory created in the previous step

 3. restart inkscape


### Under Linux

You can also run the command
```sh
    make LANG=fr very-clean install
```
or
```sh
    make LANG=en very-clean install
```
to remove a previous installation of the extension and install the current
version.

This command should be run from a terminal, from the root of the `dynalab_ext`
repository.


The command
```sh
    make LANG=fr archive
```
will create an `archive-fr.zip` that can be uncompressed inside Inkscape's
user extension directory.


Contributors
------------

The initial POC for this extension was written by
  - Cassandre Kant
  - [Morgane Farez](https://github.com/MorganeFar)
  - [Cassiopee Gossin](https://github.com/ceedjy)
  - [Lilian Cusumano](https://github.com/LilianCUSUMANO)
  - [Jassem Bakouche]( https://github.com/jassemBAKHOUCHE)
The original repository is https://github.com/jassemBAKHOUCHE/Path2Fab

The extension has been rewritten and is currently being developed by
  - [Pierre Hyvernat](https://github.com/phyver/)
The current repository is https://github.com/phyver/dynalab_ext/tree/main.


Licence
-------

This extension is released under the [GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html).
