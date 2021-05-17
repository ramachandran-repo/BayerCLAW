import logging
from typing import Generator, List

from . import state_machine_resources as sm
from .util import CoreStack, Resource, State


def handle_native_step(core_stack: CoreStack,
                       step_name: str,
                       spec: dict,
                       wf_params: dict,
                       map_depth: int) -> Generator[Resource, None, List[State]]:
    logger = logging.getLogger(__name__)
    logger.info(f"making native step {step_name}")

    ret = spec.copy()

    if spec["Type"] == "Parallel":
        sub_branches = []

        for branch in spec["Branches"]:
            sub_branch = yield from sm.make_branch(core_stack, branch["steps"], wf_params, depth=map_depth)
            sub_branches.append(sub_branch)

        ret.update({"Branches": sub_branches})

    try:
        # if this native step was generated by the compiler, don't modify ResultPath or OutputPath
        ret.pop("_stet")

    except KeyError:
        if spec["Type"] not in {"Wait", "Succeed", "Fail"}:
            ret.update({"ResultPath": None})

        if spec["Type"] != "Fail":
            ret.update({"OutputPath": "$"})

    return [State(step_name, ret)]
