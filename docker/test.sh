trap 'exit 1' ERR

# travis test script for django app

# start virtualenv
source bin/activate

# install test tooling
pip install pycodestyle coverage
apt-get install -y nodejs npm
npm install -g jshint

function join_by { 
    local d=${1-} f=${2-}; if shift 2; then printf %s "$f" "${@/#/$d}"; fi;
}

function run_test {
    echo "##########################"
    echo "TEST: $1"
    eval $1
}

app_array=("analytics"  "data_aggregator")

for app_name in "${app_array[@]}"; do
    if [[ -d ${app_name}/static/${app_name}/js ]]; then
        run_test "jshint ${app_name}/static/${app_name}/js --verbose"
    elif [[ -d ${app_name}/static/js ]]; then
        run_test "jshint ${app_name}/static/js --verbose"
    fi
    run_test "pycodestyle ${app_name}/ --exclude=migrations,static"
    run_test "coverage run -p --source=${app_name} manage.py test ${app_name}"
done

# put generated coverage result where it will get processed
cp .coverage.* /coverage

exit 0
