DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR

python util/gen_js_sdk.py util/test/hello-message.yaml > util/test/gen_js_sdk/hello-message.js
python util/gen_js_sdk.py util/test/todo-list.yaml > util/test/gen_js_sdk/todo-list.js
python util/gen_js_sdk.py util/test/dog-tracker.yaml > util/test/gen_js_sdk/dog-tracker.js
python util/gen_js_sdk.py util/test/property-tracker.yaml > util/test/gen_js_sdk/property-tracker.js