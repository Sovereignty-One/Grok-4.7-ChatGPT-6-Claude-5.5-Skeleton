import asyncio
import pytest

from integration.parallel_fanout import parallel_fanout


class ValidAuthorization:
    def is_valid_for(self, task_id):
        return task_id == "task-1"


class InvalidAuthorization:
    def is_valid_for(self, task_id):
        return False


def test_missing_authorization_fails_before_provider_calls():
    called = []
    async def provider(payload):
        called.append(True)
        return "output"
    with pytest.raises(PermissionError):
        asyncio.run(parallel_fanout(
            task_id="task-1", payload={"intent": "test"},
            authorization=InvalidAuthorization(), providers={"local": provider},
            authorization_verifier=lambda _auth, _task: True
        ))
    assert called == []


def test_providers_fan_out_and_results_keep_provider_identity():
    async def alpha(payload):
        await asyncio.sleep(0.01)
        return {"answer": "A"}
    async def beta(payload):
        return {"answer": "B"}
    results = asyncio.run(parallel_fanout(
        task_id="task-1", payload={"intent": "test"},
        authorization=ValidAuthorization(),
        authorization_verifier=lambda auth, task: auth.is_valid_for(task),
        providers={"alpha": alpha, "beta": beta}, max_concurrency=2
    ))
    assert [r.provider_id for r in results] == ["alpha", "beta"]
    assert all(r.status == "completed" and len(r.output_digest) == 64 for r in results)


def test_provider_failure_is_isolated():
    async def broken(payload):
        raise RuntimeError("private detail must not leak")
    async def healthy(payload):
        return "ok"
    results = asyncio.run(parallel_fanout(
        task_id="task-1", payload={},
        authorization=ValidAuthorization(),
        authorization_verifier=lambda auth, task: auth.is_valid_for(task),
        providers={"broken": broken, "healthy": healthy}
    ))
    assert results[0].status == "failed"
    assert results[0].error_code == "RuntimeError"
    assert results[1].status == "completed"


def test_invalid_concurrency_rejected():
    with pytest.raises(ValueError):
        asyncio.run(parallel_fanout(
            task_id="task-1", payload={}, authorization=ValidAuthorization(),
            providers={"local": lambda _: asyncio.sleep(0)}, max_concurrency=0,
            authorization_verifier=lambda auth, task: auth.is_valid_for(task)
        ))


def test_missing_crypto_verifier_denies_even_task_bound_object():
    async def provider(payload):
        return "must-not-run"
    with pytest.raises(PermissionError, match="cryptographic verification"):
        asyncio.run(parallel_fanout(
            task_id="task-1", payload={}, authorization=ValidAuthorization(),
            providers={"local": provider},
        ))
