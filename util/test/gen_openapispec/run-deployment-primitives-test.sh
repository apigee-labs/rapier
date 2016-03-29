DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
#echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
#echo $ROOT_DIR
./util/gen_openapispec.py util/test/deployment-primitives.yaml > util/test/gen_openapispec/deployment-primitives.yaml