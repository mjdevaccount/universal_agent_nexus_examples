# Universal Agent Stack API Reference

*Generated: 2025-12-06T04:40:18.694587*

## Introduction

# Introduction

The Universal Agent Stack is a comprehensive framework designed to build, assemble, and translate agent definitions into runtime code. This API reference provides detailed information about the stack's architecture, repositories, and key APIs.

## Architecture Overview

# Architecture Overview

The Universal Agent Stack is composed of several key components, each serving a specific purpose:

- **Composition Layer**: Builds and assembles agent definitions.
- **Reference Architecture**: Provides design patterns and templates for the stack.
- **Compiler/Translator**: Converts agent definitions into runtime code.

## Repositories

# Repositories

The Universal Agent Stack consists of the following repositories:

- **universal_agent_fabric**: Composition Layer - Builds and assembles agent definitions.
- **universal_agent_architecture**: Reference Architecture - Design patterns and templates.
- **universal_agent_nexus**: Compiler/Translator - Converts agent definitions to runtime code.
- **universal_agent_nexus_examples**: Examples for the Compiler/Translator.

## API Surface

# API Surface

The following APIs are available in the Universal Agent Stack:

- **universal_agent_fabric**:
  - `tests/test_builder.py`
  - `universal_agent_fabric/builder.py`

- **universal_agent_architecture**:
  - Adapters: `adapters/mcp/client.py`

- **universal_agent_nexus**:
  - Core Modules: `adapters/langgraph/compiler.py`, `lambda/tool_processor/main.py`, etc.
  - Adapters: `adapters/aws/bedrock.py`, `adapters/aws/dynamodb.py`, etc.

- **universal_agent_nexus_examples**:
  - Examples: `06-playground-simulation/backend/fabric_compiler.py`, `07-innovation-waves/backend/main.py`, etc.
