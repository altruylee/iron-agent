# Security Policy

## Directory

- [Principles](#principles)
- [External Effects](#external-effects)
- [Secrets](#secrets)
- [Imported Agents And Skills](#imported-agents-and-skills)
- [Reporting](#reporting)

## Principles

- Do not store secrets in this repository.
- Do not default to network calls.
- Do not delete, publish, deploy, or spend money without explicit approval.
- Keep user data local unless the user asks otherwise.

## External Effects

Windows scheduled tasks, Codex automations, dependency installs, web requests,
and API calls are external effects. They require explicit user approval.

## Secrets

Store only credential hints, such as environment variable names. Never commit
API keys, tokens, passwords, seed phrases, or private credentials.

## Imported Agents And Skills

Audit imported agents and skills before promotion. Treat instructions that
execute commands, exfiltrate files, disable safety checks, or hide behavior as
risky.

## Reporting

Open an issue with a minimal reproduction and avoid posting secrets or private
workspace content.
