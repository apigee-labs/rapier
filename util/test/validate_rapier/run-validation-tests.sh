DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./rapier/util/validate_rapier.py rapier/util/test/validate_rapier/hello-message.yaml 2> rapier/util/test/validate_rapier/hello-message-errors.yaml
./rapier/util/validate_rapier.py rapier/util/test/todo-list-basic.yaml
#./rapier/util/validate_rapier.py rapier/util/test/todo-list-with-id.yaml
#./rapier/util/validate_rapier.py rapier/util/test/todo-list-with-self.yaml
#./rapier/util/validate_rapier.py rapier/util/test/todo-list-with-links.yaml
#./rapier/util/validate_rapier.py rapier/util/test/dog-tracker.yaml
#./rapier/util/validate_rapier.py rapier/util/test/property-tracker.yaml
#./rapier/util/validate_rapier.py rapier/util/test/spec-hub.yaml
#./rapier/util/validate_rapier.py rapier/util/test/spec-hub.yaml
#./rapier/util/validate_rapier.py rapier/util/test/ssl.yaml
#./rapier/util/validate_rapier.py rapier/util/test/deployment.yaml
#./rapier/util/validate_rapier.py rapier/util/test/site-webmaster.yaml
#./rapier/util/validate_rapier.py rapier/util/test/deployment-primitives.yaml
#./rapier/util/validate_rapier.py rapier/util/test/deployment-primitives-simplified.yaml
