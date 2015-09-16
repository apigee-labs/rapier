DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
cd $DIR
$DIR/helloMessage/run_tests.sh
$DIR/todoList/run_tests.sh