DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR

python rapier/gen_swagger/gen_swagger.py rapier/test/hello-message.yaml > rapier/test/gen_swagger/swagger-hello-message.yaml
python rapier/gen_swagger/gen_swagger.py rapier/test/todo-list.yaml > rapier/test/gen_swagger/swagger-todo-list.yaml
python rapier/gen_swagger/gen_swagger.py rapier/test/dog-tracker.yaml > rapier/test/gen_swagger/swagger-dog-tracker.yaml
python rapier/gen_swagger/gen_swagger.py rapier/test/property-tracker.yaml > rapier/test/gen_swagger/swagger-property-tracker.yaml
python rapier/gen_swagger/gen_swagger.py rapier/test/spec-hub.yaml > rapier/test/gen_swagger/swagger-spec-hub.yaml