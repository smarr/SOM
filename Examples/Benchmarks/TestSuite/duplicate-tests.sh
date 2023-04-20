#!/bin/sh
echo "Currently, we can only do up to 10 classes, because otherwise, we have too many literals in a single method"
for i in $(seq 1 100)
do
  echo $i

  TESTS=("Array" "Block" "Boolean" "ClassLoading" "ClassStructure" "Closure" "Coercion"
         "CompilerReturn" "Dictionary" "DoesNotUnderstand" "Double" "Empty" "Global"
         "Hash" "Integer" "Preliminary" "Reflection" "SelfBlock" "Set" "SpecialSelectors"
         "String"
         "Super" "Symbol" "System" "Vector")
  
  for name in ${TESTS[@]}
  do
    cp "${name}Test.som" "${name}${i}Test.som"
    sed -i '' "s/${name}Test =/${name}${i}Test =/g" "${name}${i}Test.som"
  done

  # Create TestGC${i}.som
  TEST_GC_FILE="TestGC${i}.som"
  TEST_GC_CLASS="TestGC${i}"

  echo "${TEST_GC_CLASS} = TestGCCommon (" >  "${TEST_GC_FILE}"
  echo "  tests = ("                       >> "${TEST_GC_FILE}"
  echo "    | v |"                         >> "${TEST_GC_FILE}"
  echo "    v := Vector new."              >> "${TEST_GC_FILE}"
  for j in $(seq 1 "$i")
  do
    echo "    self tests${j}: v."          >> "${TEST_GC_FILE}"
  done
  echo "    ^ v"                           >> "${TEST_GC_FILE}"
  echo "  )"                               >> "${TEST_GC_FILE}"
  echo ""                                  >> "${TEST_GC_FILE}"

  for j in $(seq 1 "$i")
  do
    echo "  tests${j}: v = ("              >> "${TEST_GC_FILE}"

    for name in ${TESTS[@]}
    do
      echo "    v append: ${name}${j}Test.">> "${TEST_GC_FILE}"
    done
    echo "  )"                             >> "${TEST_GC_FILE}"
    echo ""                                >> "${TEST_GC_FILE}"
  done
  echo ")"                                 >> "${TEST_GC_FILE}"

  # Create Test${i}.som
  TEST_FILE="Test${i}.som"
  TEST_CLASS="Test${i}"

  echo "${TEST_CLASS} = TestCommon ("      >  "${TEST_FILE}"
  echo "  numExecs = ("                    >> "${TEST_FILE}"
  echo "    ^ $i"                          >> "${TEST_FILE}"
  echo "  )"                               >> "${TEST_FILE}"
  echo ""                                  >> "${TEST_FILE}"
  echo "  tests = ("                       >> "${TEST_FILE}"
  echo "    | v |"                         >> "${TEST_FILE}"
  echo "    v := Vector new."              >> "${TEST_FILE}"
  for j in $(seq 1 "$i")
  do
    echo "    self tests${j}: v."          >> "${TEST_FILE}"
  done
  echo "    ^ v"                           >> "${TEST_FILE}"
  echo "  )"                               >> "${TEST_FILE}"
  echo ""                                  >> "${TEST_FILE}"

  for j in $(seq 1 "$i")
  do
    echo "  tests${j}: v = ("              >> "${TEST_FILE}"

    for name in ${TESTS[@]}
    do
      echo "    v append: ${name}${j}Test.">> "${TEST_FILE}"
    done
    echo "  )"                             >> "${TEST_FILE}"
    echo ""                                >> "${TEST_FILE}"
  done
  echo ")"                                 >> "${TEST_FILE}"

done
