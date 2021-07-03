trap 'exit 1' ERR

# travis test script for django app

# start virtualenv
source bin/activate

# install test tooling
pip install pycodestyle coverage
apt-get install -y nodejs npm
npm install -g jshint

function run_test {
    echo "##########################"
    echo "TEST: $1"
    eval $1
}

AppArray=("analytics"  "data_aggregator")

for APP_NAME in ${AppArray[*]}; do
    run_test "pycodestyle ${APP_NAME}/ --exclude=migrations,static"

    if [ -d ${APP_NAME}/static/${APP_NAME}/js ]; then
        run_test "jshint ${DJANGO_APP}/static/${DJANGO_APP}/js --verbose"
    elif [ -d ${APP_NAME}/static/js ]; then
        run_test "jshint ${APP_NAME}/static/js --verbose"
    fi

    run_test "coverage run --source=${APP_NAME} '--omit=*/migrations/*' manage.py test ${APP_NAME}"

    # put generated coverage result where it will get processed
    cp .coverage.* /coverage
done

exit 0
