import asyncio
import logging
from datetime import datetime
from random import randint

import time
from frozendict import frozendict

from camunda.external_task.external_task import ExternalTask
from camunda.external_task.external_task_worker import ExternalTaskWorker
from camunda.utils.log_utils import log_with_context

logger = logging.getLogger(__name__)

default_config = frozendict({
    "maxTasks": 1,
    "lockDuration": 10000,
    "asyncResponseTimeout": 5000,
    "retries": 3,
    "retryTimeout": 5000,
    "sleepSeconds": 30
})


async def main():
    configure_logging()

    loop = asyncio.get_event_loop()
    tasks = []
    for topic in ["PARALLEL_STEP_1", "PARALLEL_STEP_2", "COMBINE_STEP"]:
        task = loop.create_task(ExternalTaskWorker(config=default_config).subscribe(topic, handle_task))
        tasks.append(task)

    await asyncio.gather(*tasks)


def configure_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.StreamHandler()])


async def handle_task(task: ExternalTask):
    log_context = frozendict({"WORKER_ID": task.get_worker_id(), "TASK_ID": task.get_task_id(),
                              "TOPIC": task.get_topic_name()})
    log_with_context("handle_task started", log_context)

    # simulate task execution
    execution_time = randint(0, 10)
    log_with_context(f"handle_task - business logic execution started for task: "
                     f"it will execute for {execution_time} seconds", log_context)
    await asyncio.sleep(execution_time)

    # simulate that task results randomly into failure/BPMN error/complete
    failure = random_true()
    bpmn_error = False if failure else random_true()
    # override the values to simulate success/failure/BPMN error explicitly (if needed)
    failure, bpmn_error = False, False
    log_with_context(f"handle_task - business logic executed: failure: {failure}, bpmn_error: {bpmn_error}",
                     log_context)

    return await __handle_task_result(task, failure, bpmn_error)


async def __handle_task_result(task, failure, bpmn_error):
    if failure:
        return task.failure("task failed", "failed task details", 3, 5000)
    elif bpmn_error:
        return task.bpmn_error("BPMN_ERROR_CODE")
    return task.complete({"success": True, "task_completed_on": str(datetime.now())})


def random_true():
    current_milli_time = lambda: int(round(time.time() * 1000))
    return current_milli_time() % 2 == 0


if __name__ == '__main__':
    asyncio.run(main())
