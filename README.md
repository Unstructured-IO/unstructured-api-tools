<h3 align="center">
  <img
    src="https://raw.githubusercontent.com/Unstructured-IO/unstructured-api-tools/main/img/unstructured_logo.png"
    height="200"
  >
</h3>

<h3 align="center">
  <p>Open-Source Pre-Processing Tools for Unstructured Data</p>
</h3>


The `unstructured_api_tools` library includes utilities for converting pipeline notebooks into
REST API applications. `unstructured_api_tools` is intended for use in conjunction with
pipeline repos. See [`pipeline-sec-filings`](https://github.com/Unstructured-IO/pipeline-sec-filings)
for an example of a repo that uses `unstructured_api_tools`.

## Installation

To install the library, run `pip install unstructured_api_tools`.

## Developer Quick Start

* Using `pyenv` to manage virtualenv's is recommended
	* Mac install instructions. See [here](https://github.com/Unstructured-IO/community#mac--homebrew) for more detailed instructions.
		* `brew install pyenv-virtualenv`
	  * `pyenv install 3.8.15`
  * Linux instructions are available [here](https://github.com/Unstructured-IO/community#linux).

* Create a virtualenv to work in and activate it, e.g. for one named `unstructured_api_tools`:

	`pyenv  virtualenv 3.8.15 unstructured_api_tools` <br />
	`pyenv activate unstructured_api_tools`

* Run `make install-project-local`

## Usage

Use the CLI command to convert pipeline notebooks to scripts, for example:

```bash
unstructured_api_tools convert-pipeline-notebooks \
  --input-directory pipeline-family-sec-filings/pipeline-notebooks \
  --output-directory pipeline-family-sec-filings/prepline_sec_filings/api \
  --pipeline-family sec-filings \
  --semver 0.2.1
```

If you do not provide the `pipeline-family` and `semver` arguments, those values are parsed from
`preprocessing-pipeline-family.yaml`. You can provide the `preprocessing-pipeline-family.yaml` file
explicitly with `--config-filename` or the `PIPELINE_FAMILY_CONFIG` environment variable. If neither
of those is specified, the fallback is to use the `preprocessing-pipeline-family.yaml` file in the
current working directory.

The API file undergoes `black`, `flake8` and `mypy` checks after being generated. If you want
`flake8` to ignore specific errors, you can specify them through the CLI with
`--flake8-ignore F401, E402`.
See the [`flake8` docs](https://flake8.pycqa.org/en/latest/user/error-codes.html#error-violation-codes)
for a full list of error codes.

### Conversion from `pipeline_api` to FastAPI

The command described in [**Usage**](#Usage) generates a FastAPI API route for each `pipeline_api`
function defined in the notebook. The signature of the `pipeline_api` method determines what
parameters the generated FastAPI accepts.

Currently, only plain text file uploads are supported and as such the first argument must always be
`text`, but support for multiple files and binary files is coming soon!

In addition, any number of string array parameters may be specified. Any kwarg beginning with
`m_` indicates a multi-value string parameter that is accepted by the FastAPI API.

For example, in a notebook containing:

    def pipeline_api(text, m_subject=[], m_name=[]):

`text` represents the content of a file posted to the FastAPI API, and the `m_subject` and `m_name`
keyword args represent optional parameters that may be posted to the API as well, both allowing
multiple string parameters. A `curl` request against such an API could look like this:

    curl -X 'POST' \
      'https://<hostname>/<pipeline-family-name>/<pipeline-family-version>/<api-name>' \
      -H 'accept: application/json'  \
      -H 'Content-Type: multipart/form-data' \
      -F 'file=@file-to-process.txt' \
      -F 'subject=art' \
      -F 'subject=history'
      -F 'subject=math' \
      -F 'name=feynman'

In addition, you can specify the response type if `pipeline_api` can support both "application/json"
and "text/csv" as return types.

For example, in a notebook containing a kwarg `response_type`:

    def pipeline_api(text, response_type="text/csv", m_subject=[], m_name=[]):

The consumer of the API may then specify "text/csv" as the requested response content type with the usual
HTTP Accept header, e.g. `Accept: application/json` or `Accept: text/csv`.

## Security Policy

See our [security policy](https://github.com/Unstructured-IO/unstructured-api-tools/security/policy) for
information on how to report security vulnerabilities.

## Learn more

| Section | Description |
|-|-|
| [Company Website](https://unstructured.io) | Unstructured.io product and company info |
