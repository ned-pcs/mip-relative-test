import test_support as ts
import mip

mip.install('github:ned-pcs/mip-relative-test')

ts.ls_test_files()
ts.rm_test_files()