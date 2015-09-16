DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
echo $ROOT_DIR
python util/gen_py_sdk.py util/test/hello-message.yaml > util/test/gen_py_sdk/hello-message.py
python util/gen_py_sdk.py util/test/todo-list.yaml > util/test/gen_py_sdk/todo-list.py
python util/gen_py_sdk.py util/test/dog-tracker.yaml > util/test/gen_py_sdk/dog-tracker.py
python util/gen_py_sdk.py util/test/property-tracker.yaml > util/test/gen_py_sdk/property-tracker.py