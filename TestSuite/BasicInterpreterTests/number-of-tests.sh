#!/bin/sh
SCRIPT_PATH=`dirname $0`
TEST_FILE="${SCRIPT_PATH}/NumberOfTests.som"

# find all tests, count them, trim whitespace from result
NUM_TESTS=`grep -R "test[^[:space:]]*[[:space:]]\+= (" "${SCRIPT_PATH}" | wc -l | tr -d '[:space:]'`

TEST_CODE="    numberOfTests = ( ^ ${NUM_TESTS} )"

sed -i'.old' -e 's/.*numberOfTests.*/'"${TEST_CODE}/" "${TEST_FILE}"

git --no-pager diff --exit-code "${TEST_FILE}"
