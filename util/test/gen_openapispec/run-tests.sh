DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./util/gen_openapispec.py util/test/hello-message.yaml > util/test/gen_openapispec/openapispec-hello-message.yaml
./util/gen_openapispec.py util/test/todo-list-basic.yaml > util/test/gen_openapispec/openapispec-todo-list-basic.yaml
./util/gen_openapispec.py util/test/todo-list-with-id.yaml > util/test/gen_openapispec/openapispec-todo-list-with-id.yaml
./util/gen_openapispec.py util/test/todo-list-with-self.yaml > util/test/gen_openapispec/openapispec-todo-list-with-self.yaml
./util/gen_openapispec.py util/test/todo-list-with-links.yaml > util/test/gen_openapispec/openapispec-links-todo-list.yaml
./util/gen_openapispec.py util/test/dog-tracker.yaml > util/test/gen_openapispec/openapispec-dog-tracker.yaml
./util/gen_openapispec.py util/test/property-tracker.yaml > util/test/gen_openapispec/openapispec-property-tracker.yaml
./util/gen_openapispec.py util/test/spec-hub.yaml > util/test/gen_openapispec/openapispec-spec-hub.yaml
./util/gen_openapispec.py -is util/test/spec-hub.yaml > util/test/gen_openapispec/openapispec-spec-hub-with-impl.yaml
./util/gen_openapispec.py -s util/test/ssl.yaml > util/test/gen_openapispec/openapispec-ssl.yaml
./util/gen_openapispec.py util/test/deployment.yaml > util/test/gen_openapispec/openapispec-deployment.yaml
./util/gen_openapispec.py util/test/site-webmaster.yaml > util/test/gen_openapispec/openapispec-site-webmaster.yaml
./util/gen_openapispec.py util/test/deployment-primitives.yaml > util/test/gen_openapispec/openapispec-deployment-primitives.yaml
./util/gen_openapispec.py util/test/deployment-primitives-simplified.yaml > util/test/gen_openapispec/openapispec-deployment-primitives-simplified.yaml
./util/gen_openapispec.py util/test/petstore.yaml > util/test/gen_openapispec/openapispec-petstore.yaml
./util/gen_openapispec.py util/test/build-and-push.yaml > util/test/gen_openapispec/openapispec-build-and-push.yaml
./util/gen_openapispec.py util/test/build.yaml > util/test/gen_openapispec/openapispec-build.yaml
