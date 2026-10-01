# CI coverage

[Python syntax / config validation](workflows/python-syntax-config.yml) runs on
pushes, pull requests, and manual dispatch using Python 3.12 on a hosted Linux
runner, with a five-minute job timeout.

- Compiles the bytes of every Git-tracked `.py` file in memory without importing
  or executing application code or writing bytecode. Fails if no Python files
  are tracked. Source encoding declarations are respected.
- Parses only `config/config.json`
  as JSON, rejecting malformed JSON and nonstandard NaN/Infinity constants.
  This checks syntax only, not configuration schema or application semantics.
- Installs no application dependencies and uses only the Python standard library.
  Editor and development-environment JSON files are outside this check.

This is syntax validation, not runtime testing or a guarantee of Python 3.12
runtime compatibility. It does not exercise imports, dependencies, authentication,
network APIs, recording/uploading, GUIs, installers, training, or evaluation.
It does not discover tests or download models, datasets, or browsers.
