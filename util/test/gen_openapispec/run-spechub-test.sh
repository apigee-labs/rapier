DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
#echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
#echo $ROOT_DIR
./util/gen_openapispec.py util/test/spec-hub.yaml > util/test/gen_openapispec/openapispec-spec-hub.yaml
./util/gen_openapispec.py -is util/test/spec-hub.yaml > util/test/gen_openapispec/openapispec-spec-hub-with-impl.yaml