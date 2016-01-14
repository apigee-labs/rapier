DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./rapier/util/gen_swagger.py rapier/util/test/property-tracker.yaml > rapier/util/test/gen_swagger/swagger-property-tracker.yaml