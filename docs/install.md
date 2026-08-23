# Installing

## Everything

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install parapet
parapet doctor
```

Python 3.9 or newer. One transitive dependency, PyYAML.

## One component

Each installs and runs alone.

```bash
pip install parapet-triage     # issue and advisory routing; PyYAML only
pip install parapet-scope      # change scope; zero dependencies
pip install parapet-attrib     # cost attribution; zero dependencies
pip install parapet-record     # the schema; zero dependencies
```

Install `parapet-record` alongside any of the three analysis packages and
their records gain input hashes and an environment profile. Without it
they still write records, marked as unverifiable.

## Optional extras

Only `parapet-triage` has any, and neither is needed for a working
install.

```bash
pip install 'parapet-triage[nlp]'      # spaCy: part of speech and entities
python -m spacy download en_core_web_sm

pip install 'parapet-triage[learn]'    # scikit-learn: a trained scorer
```

`parapet-triage doctor` says which patterns run degraded without the first.
Six of the eighty performance patterns want a real tagger; the rest do not
care.

## From source

```bash
git clone https://github.com/Yutong0711/PARAPET
cd PARAPET
make install
make check
```

`make install` does editable installs of all five packages plus the test
tools. `make check` runs the tests, the bundled example, and a build.

## What you do not need

No compiler. No commercial static analyser. No model download for the
default path. No network access at run time: every input is a file you
already have, including advisory feeds.

That is deliberate. A tool a maintainer cannot install in an hour is a
tool a maintainer does not install, and the accuracy each of those choices
costs is documented in the package that makes it.

## Verifying a release

Every release carries build provenance from the GitHub Actions workflow
that produced it:

```bash
gh attestation verify parapet-0.1.0-py3-none-any.whl \
    --repo Yutong0711/PARAPET
```

Releases also ship a CycloneDX SBOM per package.

## Uninstalling

```bash
pip uninstall parapet parapet-cli parapet-triage parapet-scope \
              parapet-attrib parapet-record
```
