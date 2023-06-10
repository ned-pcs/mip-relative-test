import test_support as ts
import mip

mip.install(f'file://{ts.PACKAGE_DIR}/package.json')

ts.ls_test_files()
ts.rm_test_files()