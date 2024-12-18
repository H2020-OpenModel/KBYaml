from __future__ import annotations

from pathlib import Path
import sys

from aiida import engine, load_profile, orm

from execflow.workchains.declarative_chain import DeclarativeChain

from kbyaml.kbyaml import get_yaml

get_yaml(output="data02.yaml")

load_profile()

if __name__ == "__main__":
    workflow = sys.argv[1]
    all = {"workchain_specification": orm.SinglefileData(Path(workflow).resolve())}

    engine.run(DeclarativeChain, **all)

