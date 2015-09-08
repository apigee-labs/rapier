DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR

python rapier/gen_python_client/gen_client.py rapier/test/hello-message.yaml > rapier/test/gen_python_client/hello-message.py
python rapier/gen_python_client/gen_client.py rapier/test/todo-list.yaml > rapier/test/gen_python_client/todo-list.py
python rapier/gen_python_client/gen_client.py rapier/test/dog-tracker.yaml > rapier/test/gen_python_client/dog-tracker.py
python rapier/gen_python_client/gen_client.py rapier/test/property-tracker.yaml > rapier/test/gen_python_client/property-tracker.py