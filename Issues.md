14. **Java Run `IllegalArgumentException`**: `JavaCodeWrapper`'s `__convertArg` failed to parse `List` to `int[]` for method invocation. **Fix**: Implemented array conversion logic.
15. **Java Submit `ClassCastException`**: `_java_suite_runner` attempted `(Number)` cast on String "index" property. **Fix**: Used `Integer.parseInt(tc.get("index").toString())`.
