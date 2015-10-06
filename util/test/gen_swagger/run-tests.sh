DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
echo $ROOT_DIR
./rapier/util/gen_swagger.py rapier/util/test/hello-message.yaml > rapier/util/test/gen_swagger/swagger-hello-message.yaml
./rapier/util/gen_swagger.py rapier/util/test/todo-list.yaml > rapier/util/test/gen_swagger/swagger-todo-list.yaml
./rapier/util/gen_swagger.py rapier/util/test/dog-tracker.yaml > rapier/util/test/gen_swagger/swagger-dog-tracker.yaml
./rapier/util/gen_swagger.py rapier/util/test/property-tracker.yaml > rapier/util/test/gen_swagger/swagger-property-tracker.yaml
./rapier/util/gen_swagger.py rapier/util/test/spec-hub.yaml > rapier/util/test/gen_swagger/swagger-spec-hub.yaml
./rapier/util/gen_swagger.py -i rapier/util/test/spec-hub.yaml > rapier/util/test/gen_swagger/swagger-spec-hub-with-impl.yaml