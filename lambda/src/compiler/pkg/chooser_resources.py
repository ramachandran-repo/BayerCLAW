import jmespath
import logging
from typing import List

from .util import CoreStack, Step, State, lambda_logging_block


def choice_spec(expr_str: str, next_step: str) -> dict:
    ret = {
        "Variable": "$.choice",
        "StringEquals": expr_str,
        "Next": next_step
    }
    return ret


def handle_chooser_step(core_stack: CoreStack, step: Step) -> List[State]:
    logger = logging.getLogger(__name__)
    logger.info(f"making chooser step {step.name}")

    choice_step_name = f"{step.name}.choose"

    exprs = jmespath.search("choices[].if", step.spec)
    nexts = jmespath.search("choices[].next", step.spec)

    choices = [choice_spec(e, n) for e, n in zip(exprs, nexts)]

    task_step = {
        "Type": "Task",
        "Resource": core_stack.output("ChooserLambdaArn"),
        "Parameters": {
            "repo.$": "$.repo",
            "inputs": step.spec["inputs"],
            "expressions": exprs,
            **lambda_logging_block(step.name),
        },
        "ResultPath": "$.choice",
        "OutputPath": "$",
        "Next": choice_step_name,
    }

    next_or_end = step.next_or_end
    if "End" in next_or_end:
        raise RuntimeError("wtf")

    choice_step = {
        "Type": "Choice",
        "Choices": choices,
        "Default": next_or_end["Next"],
    }

    ret = [
        State(step.name, task_step),
        State(choice_step_name, choice_step),
    ]

    return ret
