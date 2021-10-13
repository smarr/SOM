#!/bin/sh
for i in $(seq 2 5)
do
  echo $i

  cp ArrayTest.som                 Array${i}Test.som
  cp BlockTest.som                 Block${i}Test.som
  cp BooleanTest.som               Boolean${i}Test.som
  cp ClassLoadingTest.som          ClassLoading${i}Test.som
  cp ClassStructureTest.som        ClassStructure${i}Test.som
  cp ClosureTest.som               Closure${i}Test.som
  cp CoercionTest.som              Coercion${i}Test.som
  cp CompilerReturnTest.som        CompilerReturn${i}Test.som
  cp DictionaryTest.som            Dictionary${i}Test.som
  cp DoesNotUnderstandTest.som     DoesNotUnderstand${i}Test.som
  cp DoubleTest.som                Double${i}Test.som
  cp EmptyTest.som                 Empty${i}Test.som
  cp GlobalTest.som                Global${i}Test.som
  cp HashTest.som                  Hash${i}Test.som
  cp IntegerTest.som               Integer${i}Test.som
  cp PreliminaryTest.som           Preliminary${i}Test.som
  cp ReflectionTest.som            Reflection${i}Test.som
  cp SelfBlockTest.som             SelfBlock${i}Test.som
  cp SetTest.som                   Set${i}Test.som
  cp SpecialSelectorsTest.som      SpecialSelectors${i}Test.som
  cp StringTest.som                String${i}Test.som
  cp SuperTest.som                 Super${i}Test.som
  cp SymbolTest.som                Symbol${i}Test.som
  cp SystemTest.som                System${i}Test.som
  cp VectorTest.som                Vector${i}Test.som

done
