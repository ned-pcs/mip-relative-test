import sys, os
from upysh import *

HOME=os.getenv('HOME')
THIS_SCRIPT=os.getcwd() + '/' + sys.argv[0]
PACKAGE_DIR=THIS_SCRIPT.rsplit( '/', 2)[-3]

print(f'HOME={HOME}, THIS_SCRIPT={THIS_SCRIPT}, PACKAGE_DIR={PACKAGE_DIR}')

TEST_FILES=('mip_test.py', 'mip_test/mip_test.py')
TEST_DIRS=('mip_test',)

def rm_test_files():
    for file in TEST_FILES:
        try:
            rm(f'{HOME}/.micropython/lib/{file}')
        except:
            pass
    for dir in TEST_DIRS:
        try:
            rmdir(f'{HOME}/.micropython/lib/{dir}')
        except:
            pass

def ls_test_files():
    for dir in TEST_DIRS:
        try:
            print(f'ls {HOME}/.micropython/lib/{dir}')
            ls(f'{HOME}/.micropython/lib/{dir}')
        except:
            pass

rm_test_files()

sys.path[0] = f'{PACKAGE_DIR}/mip_src'
import mip

try:
    import urequests
except:
    mip.install('urequests')
