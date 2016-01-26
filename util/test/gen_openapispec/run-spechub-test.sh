DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
#echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
#echo $ROOT_DIR
./rapier/util/gen_openapispec.py rapier/util/test/spec-hub.yaml > rapier/util/test/gen_openapispec/openapispec-spec-hub.yaml
./rapier/util/gen_openapispec.py -is rapier/util/test/spec-hub.yaml > rapier/util/test/gen_openapispec/openapispec-spec-hub-with-impl.yaml