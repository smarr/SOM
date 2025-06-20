import subprocess
from pathlib import Path

# testsToBeRun = ["./VecTest.som", "./Supplement.som"]
testList = [{"test": "./VecTest.som", "expected": "I AM VECTOR"}, {"test": "./Supplement.som", "expected": "I AM SUPPLEMENT"}]
location = "./core-lib/IntegrationTests/Tests"

def test_main():
    """
    Runs the main test function
    Locates the SOM++ executable and locates all compatible test files
    """
    testFiles = []
    readDirectory(location, testFiles)
    testsToBeRun = assembleTestDictionary(testFiles)
    
    # Run the tests
    runTests(testsToBeRun)

def locateTests(path, testFiles):
    """
    Locate all test files that exist in the given directory
    Return a list of paths to the test files
    """

    # To ID a file will be opened and at the top there should be a comment which starts with VM:
    for file in Path(path).glob("*.som"):
        with open(file, 'r') as f:

            # Any file with IGNORE in it will not be ran

            if "VM" in f.read() and "IGNORE" not in f.read():
                testFiles.append(file)

            if "IGNORE" in f.read():
                print(f"Test file {file} is ignored by request")

    return testFiles

def readDirectory(path, testFiles):
    """
    Recursively read all sub directories
    Path is the directory we are currently in
    testFiles is the list of test files we are building up
    """
    for directory in Path(path).iterdir():
        if directory.is_dir():
            readDirectory(directory, testFiles)
        else:
            continue

    locateTests(path, testFiles)

def assembleTestDictionary(testFiles):
    """
    Assemble a dictionary of
    name: the name of the test file
    stdout/stderr: the expected output of the test
    """
    tests = []
    for file in testFiles:
        testDict = parseTestFile(file)
        if (testDict is None):
            continue
        tests.append(testDict)
        
    return tests

def parseTestFile(testFile):
    """
    parse the test file to extract the important information
    """
    testDict = {"name": testFile, "stdout": [], "stderr": []}
    with open(testFile, 'r') as f:
        contents = f.read()
        if "IGNORE" in contents:
            print(f"Test file {testFile} is ignored by request")
            return None
        comment = contents.split("\"")[1]
        if "stdout" in comment:
            stdOut = comment.split("stdout:")[1]
            if "stderr" in stdOut:
                stdErrInx = stdOut.index("stderr:")
                stdOut = stdOut[:stdErrInx]
            stdOut = stdOut.replace("...", "")
            stdOutL = stdOut.split("\n")
            stdOutL = [line.strip() for line in stdOutL if line.strip()]
            print(f"stdout: {stdOutL}")
            testDict["stdout"] = stdOutL

        if "stderr" in comment:
            stdErr = comment.split("stderr:")[1]
            if "stdout" in stdErr:
                stdOutInx = stdErr.index("stdout:")
                stdErr = stdErr[:stdOutInx]
            stdErr = stdErr.replace("...", "")
            stdErrL = stdErr.split("\n")
            stdErrL = [line.strip() for line in stdErrL if line.strip()]  # Remove empty lines
            print(f"stderr: {stdErrL}")
            testDict["stderr"] = stdErrL

    print(f"TestDict: {testDict}")

    return testDict

    

def runTests(testsToBeRun):
    """
    Take an array of dictionaries with test file names and expected output
    Run all of the tests and report back on the results
    """

    # Define the command
    sompp_path = Path("./cmake-build/SOM++")  # Adjust if it's elsewhere or not executable
    classpath = "./core-lib/Smalltalk"

    print("\n\nRunning tests")

    for x in testsToBeRun:
        # Run the process
        result = subprocess.run(
            [str(sompp_path), "-cp", classpath, x["name"]],
            capture_output=True,
            text=True  # Decode output as string (Python 3.7+)
        )

        # SOMpp does not output to stderr
        print(f"Running test {x['name']}...")
        print(result.stdout)
        assert all(element in result.stdout for element in x['stdout']) or all(element in result.stderr for element in x['stdout']), f"Expected output ({x['stdout']}) not found in stdout for test {x['name']}"
        assert all(element in result.stderr for element in x['stderr']) or all(element in result.stdout for element in x['stderr']), f"ERROR message ({x['stderr']}) not contained in stderr for test {x['name']}"
        print(f"Test {x['name']} executed successfully")
