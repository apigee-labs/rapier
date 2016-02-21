DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./rapier/util/gen_openapispec.py rapier/util/test/hello-message.yaml > rapier/util/test/gen_openapispec/openapispec-hello-message.yaml
./rapier/util/gen_openapispec.py rapier/util/test/todo-list-basic.yaml > rapier/util/test/gen_openapispec/openapispec-todo-list-basic.yaml
./rapier/util/gen_openapispec.py rapier/util/test/todo-list-with-id.yaml > rapier/util/test/gen_openapispec/openapispec-todo-list-with-id.yaml
./rapier/util/gen_openapispec.py rapier/util/test/todo-list-with-self.yaml > rapier/util/test/gen_openapispec/openapispec-todo-list-with-self.yaml
./rapier/util/gen_openapispec.py rapier/util/test/todo-list-with-links.yaml > rapier/util/test/gen_openapispec/openapispec-links-todo-list.yaml
./rapier/util/gen_openapispec.py rapier/util/test/dog-tracker.yaml > rapier/util/test/gen_openapispec/openapispec-dog-tracker.yaml
./rapier/util/gen_openapispec.py rapier/util/test/property-tracker.yaml > rapier/util/test/gen_openapispec/openapispec-property-tracker.yaml
./rapier/util/gen_openapispec.py rapier/util/test/spec-hub.yaml > rapier/util/test/gen_openapispec/openapispec-spec-hub.yaml
./rapier/util/gen_openapispec.py -is rapier/util/test/spec-hub.yaml > rapier/util/test/gen_openapispec/openapispec-spec-hub-with-impl.yaml
./rapier/util/gen_openapispec.py -s rapier/util/test/ssl.yaml > rapier/util/test/gen_openapispec/openapispec-ssl.yaml
./rapier/util/gen_openapispec.py rapier/util/test/deployment.yaml > rapier/util/test/gen_openapispec/openapispec-deployment.yaml
./rapier/util/gen_openapispec.py rapier/util/test/site-webmaster.yaml > rapier/util/test/gen_openapispec/openapispec-site-webmaster.yaml
./rapier/util/gen_openapispec.py rapier/util/test/deployment-primitives.yaml > rapier/util/test/gen_openapispec/openapispec-deployment-primitives.yaml
./rapier/util/gen_openapispec.py rapier/util/test/deployment-primitives-simplified.yaml > rapier/util/test/gen_openapispec/openapispec-deployment-primitives-simplified.yaml
