DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
echo $ROOT_DIR
./rapier/util/gen_openapispec.py rapier/util/test/petstore.yaml > rapier/util/test/gen_openapispec/openapispec-petstore.yaml