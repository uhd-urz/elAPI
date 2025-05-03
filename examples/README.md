# eLabFTW automation examples with elAPI

We list some notable examples that showcase elAPI's capabilities, its APIs and use-cases. Many examples here have been
inspired by [elabapi-python](https://github.com/elabftw/elabapi-python/tree/master/examples)'s. The examples were
originally created for [FDM-Werkstatt 2024](https://fdm-nrw.coscine.de/#/FDM-Werkstatt).

## How the examples are structured

The examples are first categorized into `python` and `bash` directories. Each example is placed inside a group
sub-directory of its topic. Each script is heavily commented with explanations.

```bash
examples/
    python/
      - topic-A/
        - Example 1 script of topic A
        - Example 2 script of topic A
      - topic-B/
        - Example 1 script of topic B
        - Example 2 script of topic B
```

## How to use the examples

elAPI can be used as a CLI tool with Bash for simple tasks, and for more advanced tasks, as a Python library. Install
`elapi` [inside a virtual environment](https://github.com/uhd-urz/elAPI?tab=readme-ov-file#installing-elapi-as-a-library)
if you intend to write Python scripts with elAPI. Make sure elAPI is
correctly [configured](https://github.com/uhd-urz/elAPI?tab=readme-ov-file#getting-started) first. You can just clone
this entire repository, or copy/paste individual scripts. E.g., with Python examples, the script
[
`download_bulk_experiments.py`](https://github.com/uhd-urz/elAPI/blob/main/examples/download_experiments/download_bulk_experiments.py)
can be run without any modification to the script:

```bash
python examples/python/download_experiments/download_bulk_experiments.py
```

> [!TIP]
> Some entities such as "experiments" and "resources" share similar endpoints. So, if there's an example script about
> experiments, it's very likely the same script will work with resources (or items) as well.
