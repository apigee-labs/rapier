import sys
import getopt
from gen_openapispec import main as gen_oas_main
from validate_rapier import main as validate_main
from gen_js_sdk import main as gen_js_main
from gen_py_sdk import main as gen_py_main

def main():
    usage = 'usage: rapier [-v, --validate] [-p, --gen-python] [-j, --gen-js] [-m, --yaml-merge] [-i, --include-impl] [-t --suppress-templates] filename'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vpjmit', ['validate', 'gen-python', 'gen-js', 'yaml-merge', 'include-impl', 'suppress-templates'])
    except getopt.GetoptError as err:
        sys.exit(str(err) + '\n' + usage)
    if not len(args) == 1:
        sys.exit(usage)        
    opts_keys = [k for k,v in opts]

    if '-v' in opts_keys or '--validate' in opts_keys:
        validate_main(args[0])
    elif '-p' in opts_keys or '--gen-python' in opts_keys:
        gen_py_main(args[0])
    elif '-j' in opts_keys or '--gen-js' in opts_keys:
        gen_py_main(args[0])
    else:
        gen_oas_main(sys.argv)