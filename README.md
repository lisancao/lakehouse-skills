# lakehouse-skills

AI assistant skills and references for [lakehouse-stack](https://github.com/lisancao/lakehouse-at-home).

## What are Skills?

Skills are detailed reference guides that help AI assistants (like Claude) work effectively with specific technologies and patterns in the lakehouse ecosystem. They contain:

- Step-by-step guidance for common tasks
- Code patterns and examples
- Common errors and solutions
- Best practices specific to this project

## Available Skills

| Skill | Description |
|-------|-------------|
| [SDP.md](.claude/skills/SDP.md) | Spark Declarative Pipelines - from basics to production |

## Usage

### With Claude Code

Skills are automatically available when working in the lakehouse-stack repository. Reference them in your prompts:

```
Read the SDP skill and help me write a pipeline for customer data
```

### Manual Reference

Skills can be read directly as documentation for understanding patterns and approaches used in the project.

## Structure

```
.claude/
└── skills/
    └── SDP.md          # Spark Declarative Pipelines reference
CLAUDE.md               # Main project reference for AI assistants
```

## Related

- [lakehouse-stack](https://github.com/lisancao/lakehouse-at-home) - Main project repository
