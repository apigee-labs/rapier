DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)
# echo $DIR
ROOT_DIR=$( cd "$( dirname "$DIR/../../../../" )" && pwd)
cd $ROOT_DIR
# echo $ROOT_DIR
./util/gen_html.py util/test/hello-message.yaml > util/test/gen_html/hello-message.html
./util/gen_html.py util/test/todo-list-basic.yaml > util/test/gen_html/todo-list-basic.html
./util/gen_html.py util/test/todo-list-with-id.yaml > util/test/gen_html/todo-list-with-id.html
./util/gen_html.py util/test/todo-list-with-self.yaml > util/test/gen_html/todo-list-with-self.html
./util/gen_html.py util/test/todo-list-with-links.yaml > util/test/gen_html/links-todo-list.html
./util/gen_html.py util/test/dog-tracker.yaml > util/test/gen_html/dog-tracker.html
./util/gen_html.py util/test/property-tracker.yaml > util/test/gen_html/property-tracker.html
./util/gen_html.py util/test/spec-hub.yaml > util/test/gen_html/spec-hub.html
./util/gen_html.py util/test/spec-hub.yaml > util/test/gen_html/spec-hub-with-impl.html
./util/gen_html.py util/test/ssl.yaml > util/test/gen_html/ssl.html
./util/gen_html.py util/test/site-webmaster.yaml > util/test/gen_html/site-webmaster.html
./util/gen_html.py util/test/petstore.yaml > util/test/gen_html/petstore.html
./util/gen_html.py util/test/common.yaml > util/test/gen_html/common.html
