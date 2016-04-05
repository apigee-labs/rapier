DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./util/gen_openapispec.py util/test/hello-message.yaml > util/test/gen_openapispec/hello-message.yaml
./util/gen_openapispec.py util/test/todo-list-basic.yaml > util/test/gen_openapispec/todo-list-basic.yaml
./util/gen_openapispec.py util/test/todo-list-with-id.yaml > util/test/gen_openapispec/todo-list-with-id.yaml
./util/gen_openapispec.py util/test/todo-list-with-self.yaml > util/test/gen_openapispec/todo-list-with-self.yaml
./util/gen_openapispec.py util/test/todo-list-with-links.yaml > util/test/gen_openapispec/links-todo-list.yaml
./util/gen_openapispec.py util/test/dog-tracker.yaml > util/test/gen_openapispec/dog-tracker.yaml
./util/gen_openapispec.py util/test/property-tracker.yaml > util/test/gen_openapispec/property-tracker.yaml
./util/gen_openapispec.py util/test/spec-hub.yaml > util/test/gen_openapispec/spec-hub.yaml
./util/gen_openapispec.py -i util/test/spec-hub.yaml > util/test/gen_openapispec/spec-hub-with-impl.yaml
./util/gen_openapispec.py util/test/ssl.yaml > util/test/gen_openapispec/ssl.yaml
./util/gen_openapispec.py util/test/deployment.yaml > util/test/gen_openapispec/deployment.yaml
./util/gen_openapispec.py util/test/site-webmaster.yaml > util/test/gen_openapispec/site-webmaster.yaml
./util/gen_openapispec.py util/test/deployment-primitives.yaml > util/test/gen_openapispec/deployment-primitives.yaml
./util/gen_openapispec.py util/test/deployment-primitives-simplified.yaml > util/test/gen_openapispec/deployment-primitives-simplified.yaml
./util/gen_openapispec.py util/test/petstore.yaml > util/test/gen_openapispec/petstore.yaml
./util/gen_openapispec.py util/test/build-and-push.yaml > util/test/gen_openapispec/build-and-push.yaml
./util/gen_openapispec.py util/test/build.yaml > util/test/gen_openapispec/build.yaml
./util/gen_openapispec.py util/test/ams.yaml > util/test/gen_openapispec/ams.yaml
./util/gen_openapispec.py util/test/use-common.yaml > util/test/gen_openapispec/use-common.yaml
#./util/gen_openapispec.py util/test/kms.yaml > util/test/gen_openapispec/kms.yaml