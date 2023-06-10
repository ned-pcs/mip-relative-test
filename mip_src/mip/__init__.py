# MicroPython package installer
# MIT license; Copyright (c) 2022 Jim Mussared

import urequests as requests
import sys
import ujson as json

print("loading mip from local lib") # TODO: remove

_PACKAGE_INDEX = const("https://micropython.org/pi/v2")
_CHUNK_SIZE = 128
_URL_PREFIXES = const(("http://", "https://", "github:", "file://"))

# Return true if name is a URI that we understand
def _is_url(name):
    return any(name.startswith(prefix) for prefix in _URL_PREFIXES)

# This implements os.makedirs(os.dirname(path))
def _ensure_path_exists(path):
    import os

    split = path.split("/")

    # Handle paths starting with "/".
    if not split[0]:
        split.pop(0)
        split[0] = "/" + split[0]

    prefix = ""
    for i in range(len(split) - 1):
        prefix += split[i]
        try:
            os.stat(prefix)
        except:
            os.mkdir(prefix)
        prefix += "/"


# Copy from src (stream) to dest (function-taking-bytes)
def _chunk(src, dest):
    buf = memoryview(bytearray(_CHUNK_SIZE))
    while True:
        n = src.readinto(buf)
        if n == 0:
            break
        dest(buf if n == _CHUNK_SIZE else buf[:n])


# Check if the specified path exists and matches the hash.
def _check_exists(path, short_hash):
    import os

    try:
        import binascii
        import hashlib

        with open(path, "rb") as f:
            hs256 = hashlib.sha256()
            _chunk(f, hs256.update)
            existing_hash = str(binascii.hexlify(hs256.digest())[: len(short_hash)], "utf-8")
            return existing_hash == short_hash
    except:
        return False


def _rewrite_url(url, branch=None, package_json_url=None):
    if url.startswith("github:"):
        if not branch:
            branch = "HEAD"
        url = url[7:].split("/")
        url = (
            "https://raw.githubusercontent.com/"
            + url[0]
            + "/"
            + url[1]
            + "/"
            + branch
            + "/"
            + "/".join(url[2:])
        )
        return url
    # rewrite relative URLs as absolute URLs
    if not _is_url(url):
        if not package_json_url:
            raise ValueError("No package.json URL specified")
        url = package_json_url.rsplit("/", 1)[0] + "/" + url
    return url


def _download_file(url, dest):
    print(f"Downloading {url} to {dest}") # TODO: remove
    # if url is a file:// url, just copy it
    if url.startswith("file://"):
        src_name = url[7:]
        try:
            with open(src_name, "rb") as src:
                print(f"Copying file {src_name} to {dest}")
                _ensure_path_exists(dest)
                with open(dest, "wb") as dst:
                    _chunk(src, dst.write)
            return True
        except OSError:
            print(f"File {src_name} not found")
            return False

    response = requests.get(url)
    try:
        if response.status_code != 200:
            print("Error", response.status_code, "requesting", url)
            return False

        print("Copying:", dest)
        _ensure_path_exists(dest)
        with open(dest, "wb") as f:
            _chunk(response.raw, f.write)

        return True
    finally:
        response.close()


def _install_json(package_json_url, index, target, version, mpy):
    # if package_json_url is a file:// url, just download it
    # and use its json directly
    if package_json_url.startswith("file://"):
        pkg_file_name = package_json_url[7:]
        try:
            with open(pkg_file_name) as json_file:
                package_json = json.load(json_file)
        except OSError:
            print(f"File {pkg_file_name} not found")
            return False
    else:
        response = requests.get(_rewrite_url(package_json_url, version))
        try:
            if response.status_code != 200:
                print("Package not found:", package_json_url)
                return False

            package_json = response.json()
        finally:
            response.close()
    for target_path, short_hash in package_json.get("hashes", ()):
        fs_target_path = target + "/" + target_path
        if _check_exists(fs_target_path, short_hash):
            print("Exists:", fs_target_path)
        else:
            file_url = "{}/file/{}/{}".format(index, short_hash[:2], short_hash)
            if not _download_file(file_url, fs_target_path):
                print("File not found: {} {}".format(target_path, short_hash))
                return False
    for target_path, url in package_json.get("urls", ()):
        fs_target_path = target + "/" + target_path
        if not _download_file(_rewrite_url(url, version, package_json_url), fs_target_path):
            print("File not found: {} {}".format(target_path, url))
            return False
    for dep, dep_version in package_json.get("deps", ()):
        if not _install_package(dep, index, target, dep_version, mpy):
            return False
    return True


def _install_package(package, index, target, version, mpy):
    if _is_url(package):
        if package.endswith(".py") or package.endswith(".mpy"):
            print("Downloading {} to {}".format(package, target))
            return _download_file(
                _rewrite_url(package, version), target + "/" + package.rsplit("/")[-1]
            )
        else:
            if not package.endswith(".json"):
                if not package.endswith("/"):
                    package += "/"
                package += "package.json"
            print("Installing {} to {}".format(package, target))
    else:
        if not version:
            version = "latest"
        print("Installing {} ({}) from {} to {}".format(package, version, index, target))

        mpy_version = (
            sys.implementation._mpy & 0xFF if mpy and hasattr(sys.implementation, "_mpy") else "py"
        )

        package = "{}/package/{}/{}/{}.json".format(index, mpy_version, package, version)

    return _install_json(package, index, target, version, mpy)


def install(package, index=None, target=None, version=None, mpy=True):
    if not target:
        for p in sys.path:
            if p.endswith("/lib"):
                target = p
                break
        else:
            print("Unable to find lib dir in sys.path")
            return

    if not index:
        index = _PACKAGE_INDEX

    if _install_package(package, index.rstrip("/"), target, version, mpy):
        print("Done")
    else:
        print("Package may be partially installed")
