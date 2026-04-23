import json
import logging
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.harness import TaskPipeline, PipelineStep

logger = logging.getLogger(__name__)

_PLANNER_PROMPT = """You are a task planning expert. The user gives you a complex task. You must:
1. Analyze the core goal
2. Break it into executable subtasks (max 5)
3. Assign a role for each: researcher, coder, writer, analyst, or reviewer
4. Define step dependencies (use step order numbers)
5. Output an execution plan in JSON

User task: {prompt}

Respond ONLY with a JSON object:
{{
  "title": "short task title",
  "description": "brief overview",
  "steps": [
    {{
      "order": 1,
      "title": "step title",
      "description": "what this step does",
      "role": "researcher|coder|writer|analyst|reviewer",
      "depends_on": []
    }}
  ]
}}"""

_EXECUTOR_PROMPT = """You are an AI agent with the role of {role}. Complete the following task:

Task: {title}
Description: {description}
Context from previous steps:
{context}

Provide a thorough, concrete response for this specific subtask."""

_EVALUATOR_PROMPT = """Evaluate the following task output:

Task: {title}
Description: {description}
Output: {output}

Score 1-10 and provide brief notes.
Respond ONLY with JSON:
{{"score": <1-10>, "notes": "<brief evaluation>"}}"""

_SUMMARIZER_PROMPT = """Synthesize the results of a multi-step task pipeline.

Original task: {prompt}

Steps completed:
{steps_summary}

Write a concise summary (max 300 words) of what was accomplished and the key outputs."""


async def _call_llm(prompt: str, max_tokens: int = 2048) -> str:
    from app.core.http_client import get_litellm_client

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.4,
    }
    client = get_litellm_client()
    resp = await client.post("/v1/chat/completions", json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _strip_json(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:]) if len(lines) > 1 else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    return cleaned.strip()


async def plan_task(prompt: str) -> dict:
    try:
        raw = await _call_llm(_PLANNER_PROMPT.format(prompt=prompt))
        plan = json.loads(_strip_json(raw))
        if "steps" not in plan or not plan["steps"]:
            raise ValueError("No steps in plan")
        return plan
    except Exception as exc:
        logger.warning("Plan generation failed: %s", exc)
        return {
            "title": prompt[:80],
            "description": prompt,
            "steps": [
                {
                    "order": 1,
                    "title": "Execute task",
                    "description": prompt,
                    "role": "analyst",
                    "depends_on": [],
                }
            ],
        }


async def create_pipeline(db: AsyncSession, user_id: str, prompt: str) -> TaskPipeline:
    plan = await plan_task(prompt)

    pipeline = TaskPipeline(
        user_id=user_id,
        title=plan.get("title", prompt[:100]),
        description=plan.get("description"),
        status="ready",
        original_prompt=prompt,
        plan=plan,
        total_steps=len(plan.get("steps", [])),
        completed_steps=0,
    )
    db.add(pipeline)
    await db.flush()

    for step_data in plan.get("steps", []):
        step = PipelineStep(
            pipeline_id=pipeline.id,
            step_order=step_data["order"],
            title=step_data["title"],
            description=step_data.get("description"),
            agent_role=step_data["role"],
            depends_on=step_data.get("depends_on", []),
            status="pending",
        )
        db.add(step)

    await db.commit()
    await db.refresh(pipeline)
    return pipeline


async def run_pipeline(db: AsyncSession, pipeline_id: str) -> TaskPipeline:
    result = await db.execute(select(TaskPipeline).where(TaskPipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise ValueError(f"Pipeline {pipeline_id} not found")

    pipeline.status = "running"
    await db.commit()

    steps_result = await db.execute(
        select(PipelineStep)
        .where(PipelineStep.pipeline_id == pipeline_id)
        .order_by(PipelineStep.step_order)
    )
    steps = list(steps_result.scalars().all())

    completed_outputs: dict[int, str] = {}

    try:
        for step in steps:
            deps = step.depends_on or []
            if deps and not all(d in completed_outputs for d in deps):
                step.status = "skipped"
                await db.commit()
                continue

            context = "\n".join(
                f"Step {order}: {out}" for order, out in completed_outputs.items()
            ) or "No prior context."

            output = await _execute_step(db, step, context)
            if output:
                completed_outputs[step.step_order] = output

            pipeline.completed_steps = len(completed_outputs)
            await db.commit()

        steps_result2 = await db.execute(
            select(PipelineStep)
            .where(PipelineStep.pipeline_id == pipeline_id)
            .order_by(PipelineStep.step_order)
        )
        refreshed_steps = list(steps_result2.scalars().all())

        steps_summary = "\n".join(
            f"- {s.title} ({s.agent_role}): "
            + (s.output_data.get("result", "")[:300] if s.output_data else "skipped")
            for s in refreshed_steps
        )
        summary = await _call_llm(
            _SUMMARIZER_PROMPT.format(
                prompt=pipeline.original_prompt or pipeline.title,
                steps_summary=steps_summary,
            )
        )

        pipeline.result_summary = summary.strip()
        pipeline.status = "completed"
        pipeline.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(pipeline)

    except Exception as exc:
        logger.error("Pipeline %s failed: %s", pipeline_id, exc)
        pipeline.status = "failed"
        await db.commit()

    return pipeline


async def _execute_step(db: AsyncSession, step: PipelineStep, context: str) -> str:
    step.status = "running"
    step.started_at = datetime.now(timezone.utc)
    await db.commit()

    try:
        output = await _call_llm(
            _EXECUTOR_PROMPT.format(
                role=step.agent_role,
                title=step.title,
                description=step.description or "",
                context=context,
            ),
            max_tokens=2048,
        )

        step.output_data = {"result": output}
        step.status = "completed"
        step.completed_at = datetime.now(timezone.utc)

        if step.agent_role == "reviewer":
            eval_data = await _evaluate_output(step.title, step.description or "", output)
            step.evaluation_score = eval_data.get("score")
            step.evaluation_notes = eval_data.get("notes")

        await db.commit()
        return output

    except Exception as exc:
        logger.error("Step %s execution failed: %s", step.id, exc)
        step.status = "failed"
        step.output_data = {"error": str(exc)}
        await db.commit()
        return ""


async def _evaluate_output(title: str, description: str, output: str) -> dict:
    try:
        raw = await _call_llm(
            _EVALUATOR_PROMPT.format(
                title=title,
                description=description,
                output=output[:2000],
            ),
            max_tokens=256,
        )
        return json.loads(_strip_json(raw))
    except Exception as exc:
        logger.warning("Evaluation failed: %s", exc)
        return {"score": 7, "notes": "Evaluation unavailable"}


async def execute_step(db: AsyncSession, step_id: str) -> str:
    result = await db.execute(select(PipelineStep).where(PipelineStep.id == step_id))
    step = result.scalar_one_or_none()
    if not step:
        raise ValueError(f"Step {step_id} not found")
    return await _execute_step(db, step, "")


async def evaluate_step(db: AsyncSession, step_id: str) -> dict:
    result = await db.execute(select(PipelineStep).where(PipelineStep.id == step_id))
    step = result.scalar_one_or_none()
    if not step:
        return {"score": None, "notes": "Step not found"}
    output = step.output_data.get("result", "") if step.output_data else ""
    return await _evaluate_output(step.title, step.description or "", output)


async def get_pipeline_status(db: AsyncSession, pipeline_id: str) -> TaskPipeline | None:
    result = await db.execute(select(TaskPipeline).where(TaskPipeline.id == pipeline_id))
    return result.scalar_one_or_none()


async def list_pipelines(
    db: AsyncSession, user_id: str, offset: int = 0, limit: int = 20
) -> tuple[list[TaskPipeline], int]:
    total_result = await db.execute(
        select(func.count()).select_from(TaskPipeline).where(TaskPipeline.user_id == user_id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(TaskPipeline)
        .where(TaskPipeline.user_id == user_id)
        .order_by(TaskPipeline.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def cancel_pipeline(db: AsyncSession, pipeline_id: str) -> TaskPipeline | None:
    result = await db.execute(select(TaskPipeline).where(TaskPipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        return None
    if pipeline.status in ("planning", "ready", "running"):
        pipeline.status = "failed"
        await db.commit()
    return pipeline


async def list_pipeline_steps(db: AsyncSession, pipeline_id: str) -> list[PipelineStep]:
    result = await db.execute(
        select(PipelineStep)
        .where(PipelineStep.pipeline_id == pipeline_id)
        .order_by(PipelineStep.step_order)
    )
    return list(result.scalars().all())
