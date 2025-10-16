# Agent Instruction Changes - API-First Approach

## Problem Addressed

Agents were asking users for additional information instead of working with available data and providing structured outputs for API consumption.

## Changes Made

### 1. Campaign Generation Agent

**Before**: Asked for "correct image URI" when image didn't match product
**After**:

- NEVER ask for additional information
- Use any provided image URI even if it seems unrelated
- ALWAYS call both tools (image-analysis, data-enrichment)
- Generate structured campaign output regardless of data quality

### 2. Lokalize Agent

**Before**: Could ask for clarification on cultural context
**After**:

- NEVER ask for additional information
- Work with whatever content is provided
- ALWAYS provide definitive assessment (APPROPRIATE/NEEDS MODIFICATION/NOT APPROPRIATE)
- Include risk level and specific recommendations

### 3. Voice of Market Agent

**Before**: Could ask for market parameters
**After**:

- NEVER ask for additional information
- Use available brand/product data with tools
- ALWAYS provide structured analysis with action items
- Work with incomplete parameters if necessary

### 4. Supervisor Agent

**Before**: Had system instructions to ask users for missing parameters
**After**:

- Added CRITICAL OVERRIDES section to ignore system instructions about asking users
- NEVER use AgentCommunication\_\_sendMessage to ask for clarification
- ALWAYS work with available data and proceed with agent invocations
- ALWAYS return structured outputs based on agent results

## Key Principles Applied

1. **API-First**: All agents designed for API consumption, not chat interfaces
2. **Work with Available Data**: Never request additional information
3. **Structured Outputs**: Always return JSON-structured responses
4. **Graceful Degradation**: Provide useful outputs even with incomplete data
5. **Tool-First Approach**: Always use tools before generating responses

## Expected Behavior Now

- Campaign requests will always result in structured campaign output
- Cultural analysis will always provide definitive assessments
- Sentiment analysis will always include action items
- No agent will ask users for additional information
- All outputs will be API-ready structured data
