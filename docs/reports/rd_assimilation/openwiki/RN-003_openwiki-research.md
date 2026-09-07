# 🔍 Research & Evidence Trail: OpenWiki (RN-003)
## Title: OpenWiki Codebase Structure & Architecture Analysis
## Status: Active | Version: 1.0.0 | Author: Rick Scout

The OpenWiki repository is a CLI tool that generates and maintains a wiki for codebases or personal knowledge. The core architecture is built around the concept of agents reading sources, synthesizing linked Markdown wikis, and keeping them current on every change.

### Core Components

1. **CLI**: The OpenWiki CLI is the primary entry point for users. It provides various commands for initializing, updating, and interacting with the wiki.
2. **Agents**: Agents are responsible for reading sources, synthesizing linked Markdown wikis, and keeping them current on every change. They are built using the Deep Agents framework.
3. **Model Providers**: Model providers are responsible for providing the necessary models for the agents to use. There are twelve model providers out of the box, including OpenAI and Anthropic.
4. **Connectors**: Connectors are responsible for integrating with various services, such as Notion, Slack, Gmail, X, Web Search, Hacker News, and local git repositories.
5. **Interactive Visualizer**: The interactive visualizer is a feature that turns any wiki into a live, explorable node graph with a side-by-side Markdown reader.

### Dependencies & Ecosystem
- **Deep Agents Framework**
- **Model Providers (OpenAI, Anthropic, etc.)**
- **Connectors (Git, Notion, Gmail, Slack)**
- **GitHub Actions / GitLab CI / Bitbucket Pipelines**

### Component Interactions
- `CLI -> Agents`
- `Agents -> Model Providers`
- `Agents -> Connectors`
- `CLI -> CI/CD Workflows`
