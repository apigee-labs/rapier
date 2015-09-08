DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR

python rapier/gen_js_client/gen_client.py rapier/test/hello-message.yaml > rapier/test/gen_js_client/hello-message.js
python rapier/gen_js_client/gen_client.py rapier/test/todo-list.yaml > rapier/test/gen_js_client/todo-list.js
python rapier/gen_js_client/gen_client.py rapier/test/dog-tracker.yaml > rapier/test/gen_js_client/dog-tracker.js
python rapier/gen_js_client/gen_client.py rapier/test/property-tracker.yaml > rapier/test/gen_js_client/property-tracker.js