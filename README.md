This repository contains modified source code for [micropython-lib/micropython/mip](https://github.com/micropython/micropython-lib/tree/master/micropython/mip) in the `/mip_src` directory.

These modifications allow for relative file URLs as source files in the `urls` section of `package.json` files.

This modification lets you fork or check out repositories containing code to be loaded by `mip`, and test loading without changing `package.json` files.

It also contains sample filesystem data in the `/data` directory, as well as a sample `/package.json` that points to that data.

In `/scripts` there are test scripts for testing `mip` installation from a local or remote package tree.

To run these (from the top of this repository):

```
micropython -i scripts/test_local.py
```

or 

```
micropython -i scripts/test_remote.py
```