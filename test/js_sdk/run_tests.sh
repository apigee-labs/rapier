DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
echo $( cd "$( dirname "$DIR/../../.." )" && pwd)
cd "$( dirname "$DIR/../../" )"
node $DIR/run_tests.js