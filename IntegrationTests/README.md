# SOM Integration Tests

These tests are end-to-end tests, allowing us to check elements that go
beyond the language. For instance, we can test the parser, how fatal 
errors are handled, and how the VM interacts with different libraries
on the classpath.

Most of the tests come from lang_tests of
[yksom](https://github.com/softdevteam/yksom/tree/master/lang_tests).

## 1. Getting Started: Running the Integration Tests

The tests can be run using pytest by running `pytest`.

However, to run successfully, we need to set the following
environment variables. The paths have to be set relative to the
current working directory, which is where the tests are run from.

- `VM`: the path to the SOM executable
- `CLASSPATH`: the claspath, e.g., `./core-lib/Smalltalk`
- `AWFY`: the classpath for tests the use the AreWeFastYet (AWFY) 
  library, e.g., `core-lib/Examples/AreWeFastYet/Core`

Example run:

```bash
export VM=./som.sh
export CLASSPATH=./core-lib/Smalltalk
export AWFY=./core-lib/Examples/AreWeFastYet/Core
python3 -m pytest
```

At the time of writing, August 2025, most SOM implementations are
not supporting all tests, because the yksom test for behavior that
has not been specified yet.

To successfully run the tests as regression tests, most SOM
implementations come with a `TEST_EXPECTIONS` file that defines,
which tests are expected to fail.

A full example would look like this:

```bash
export VM=./som.sh
export CLASSPATH=./core-lib/Smalltalk
export AWFY=./core-lib/Examples/AreWeFastYet/Core
TEST_EXPECTATIONS=integration-tests.yml python3 -m pytest
```


## 2. Writing Tests and Expectation Files

### 2.1 Writing a Test

The integration tests are valid `.som` files that can be run by any
SOM VM.

The expected results of the tests are specified in a comment at the
top of the file, which looks like this:

```
"
VM:
    status: error
    custom_classpath: $AWFY:example/classpath:$CLASSPATH
    case_sensitive: False
    stdout:
        1000
        ...
        2 is an integer
    stderr:
        ...
        ERROR MESSAGE
"
```

The expected results are specified in a YAML-like format, which
supports the following keys:

- `status`: the expected exit code of the VM, which can be an integer,
  `success` or `error`

- `custom_classpath`: a custom classpath to be used for this test,
  which can include environment variables like `$AWFY` or `$CLASSPATH`.
  If a required environment variable is not set, the test will be
  marked as failure, reporting the missing variable.

- `case_sensitive`: can be `true` or `false` to specify whether the
  output should be checked case-sensitively or not. If not specified,
  it defaults to `false`.

- `stdout`: one or more lines that are the expected output of the
  test on standard output. Each line can contain the special
  characters `...` or `***` to specify gaps or partial word matching.
  See below for more details on how to use these.

- `stderr`: one or more lines that are the expected output of the
  test on standard error. As for `stdout`, each line can contain
  the special characters `...` or `***`.

### 2.2 Omissions and Partial Matching in Tests

Tests may not want to check for each precise bit of output.
By using `...`, omissions can be made that will not be checked.
Specifically, `...` can be used to indicate a gap, which may contain
zero or more characters, in the actual output.

Similarly, `***` can be used as part of a "word" or number.
If the output contains more characters than before the `***`,
the output has to match exactly the characters after the `***`.

However, currently, `***` cannot be used in the same line as `...`.

#### 2.2.1 Omissions with "..."

The following are a few examples of how to use `...` in tests.

##### Example 1: Omitting a line

Expectation defined in the test:

```yaml
stdout:
    Hello, World
    ...
    Goodbye
```

This would correctly accept the following two outputs.

Output 1:

```
Hello, World
Today is a Monday
Goodbye
```

Output 2:

```
Hello, World
Goodbye
```

###### Example 2: Omitting words

It can also be used in more elaborate ways, for instance, when
omitting words. However, the given words still most be present to
pass the test.

```yaml
stdout:
    Hello, ... sample ...
    ... is ... this line
    ... little ...
```

This would accept the following output:

```
Hello, this is some sample output
There is some more on this line
And a little more here
```

#### 2.2.2 Partial Matching with "***"

To partially match a word or number, but be able to accept additional
*precision*, we can use `***` in the expected output.

A number or word is any connected string of alphanumeric characters.
Using `***` in the number/word means:

1. All numbers/characters before `***` must be present.
2. The characters after `***` do not have to be present, but if they 
   are present, they must match exactly.
3. There cannot be more characters than specified.

This is particularly useful to testing the output of floating point
calculations. Different languages have different default levels of
precision, which makes floating point output platform-specific.

Let's assume the following expected output in a test:

```yaml
stdout:
    1.111***123
```

This will accept any of the following outputs:

- `1.111`
- `1.1111`
- `1.11112`
- `1.111123`

However, it will not accept the following:

- `1.1`
- `1.11`
- `1.111124`
- `1.1111234`


### 2.3 Expectation Files

Expectation files are YAML files that can be used to mark tests as
`known_failures`, `failing_as_unspecified`, `unsupported` or
`do_not_run`.

To help SOM implementers to get started, an expectation file can be
generated based on the test results obtained during a run.

By setting the `GENERATE_EXPECTATIONS_FILE` environment variable.
Setting this environment variable will also print out how many tests
passed, which tests passed that were not expected to and which tests
failed.

Tests are identified by their path relative to the test runner,
i.e., from within the `IntegrationTests` directory.

A minimal valid file could look like this:

```yaml
known_failures:
  - Tests/test.som
```

The maining of the different keys is as follows:

 - `known_failures`: these tests are expected to fail
 - `failing_as_unspecified`: these tests are expected to fail, but
    SOM is assumed to not yet specify the expected behaviour.
  - `unsupported`: these tests are expected to fail because the
    relevant SOM implementation does not intend to support this 
    feature. 
  - `do_not_run`: these tests will not be run, and it is not known
    whether they will fail or not.
    
## 3. Developing the test_runner

To run the tests of the `test_runner` itself, run `pytest -m tester`.
This will set the marker expression to `tester`, which prevents the
tests from being deselected. By default, we do not run them and only
run the SOM tests.

```bash
pytest -m tester
```
