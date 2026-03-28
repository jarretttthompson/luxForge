"""Mapping rules CRUD routes."""

import uuid

from fastapi import APIRouter, HTTPException

from src.api import dependencies as deps
from src.api.schemas import (
    MappingRuleCreate,
    MappingRuleListResponse,
    MappingRuleResponse,
    MappingRuleUpdate,
    ParameterInfo,
    ParameterListResponse,
)
from src.mapping.types import MappingRule

router = APIRouter(prefix="/api/mappings", tags=["mappings"])


def _rule_to_response(rule: MappingRule) -> MappingRuleResponse:
    return MappingRuleResponse(
        id=rule.id,
        name=rule.name,
        input_param=rule.input_param,
        output_param=rule.output_param,
        transform_chain=rule.transform_chain,
        condition=rule.condition,
        enabled=rule.enabled,
    )


@router.get("", response_model=MappingRuleListResponse)
async def list_rules():
    engine = deps.get_mapping_engine()
    rules = engine.get_rules()
    return MappingRuleListResponse(rules=[_rule_to_response(r) for r in rules])


@router.post("", response_model=MappingRuleResponse, status_code=201)
async def create_rule(body: MappingRuleCreate):
    engine = deps.get_mapping_engine()
    rule = MappingRule(
        id=str(uuid.uuid4()),
        name=body.name,
        input_param=body.input_param,
        output_param=body.output_param,
        transform_chain=body.transform_chain,
        condition=body.condition,
        enabled=body.enabled,
    )
    engine.add_rule(rule)
    return _rule_to_response(rule)


@router.get("/{rule_id}", response_model=MappingRuleResponse)
async def get_rule(rule_id: str):
    engine = deps.get_mapping_engine()
    for rule in engine.get_rules():
        if rule.id == rule_id:
            return _rule_to_response(rule)
    raise HTTPException(404, "Rule not found")


@router.put("/{rule_id}", response_model=MappingRuleResponse)
async def update_rule(rule_id: str, body: MappingRuleUpdate):
    engine = deps.get_mapping_engine()
    existing = None
    for rule in engine.get_rules():
        if rule.id == rule_id:
            existing = rule
            break
    if existing is None:
        raise HTTPException(404, "Rule not found")

    if body.name is not None:
        existing.name = body.name
    if body.input_param is not None:
        existing.input_param = body.input_param
    if body.output_param is not None:
        existing.output_param = body.output_param
    if body.transform_chain is not None:
        existing.transform_chain = body.transform_chain
        # Rebuild the transform chain
        from src.mapping.transforms import build_transform_chain
        engine._chains[rule_id] = build_transform_chain(existing.transform_chain)
    if body.condition is not None:
        existing.condition = body.condition
    if body.enabled is not None:
        existing.enabled = body.enabled

    return _rule_to_response(existing)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: str):
    engine = deps.get_mapping_engine()
    engine.remove_rule(rule_id)


@router.get("/parameters/list", response_model=ParameterListResponse)
async def list_parameters():
    registry = deps.get_param_registry()
    inputs = [ParameterInfo(name=name) for name in registry.inputs]
    outputs = [ParameterInfo(name=name) for name in registry.outputs]
    return ParameterListResponse(inputs=inputs, outputs=outputs)
