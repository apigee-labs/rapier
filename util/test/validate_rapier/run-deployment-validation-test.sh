DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./rapier/util/validate_rapier.py rapier/util/test/deployment.yaml