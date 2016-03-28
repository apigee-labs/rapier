DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
#echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
#echo $ROOT_DIR
./util/gen_openapispec.py util/test/use-common.yaml > util/test/gen_openapispec/openapispec-use-common.yaml