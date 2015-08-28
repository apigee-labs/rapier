DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../../" )" && pwd)
export PYTHONPATH=$ROOT_DIR:$PYTHONPATH
python "$DIR/test.py"