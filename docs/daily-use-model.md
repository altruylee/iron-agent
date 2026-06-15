# Daily Use Model

## Directory

- [Purpose](#purpose)
- [Live Conversation Flow](#live-conversation-flow)
- [Routing Hit](#routing-hit)
- [Routing Miss](#routing-miss)
- [Nightly Organization](#nightly-organization)
- [User Value](#user-value)

## Purpose

Iron Agent stores daily accumulated prompts, rules, SOPs, preferences, and
stable memory. Its job is to save tokens and make large models behave as if
they understand the user better.

## Live Conversation Flow

```text
User request
-> run memory_router.py
-> hit: read 1-5 prompt/rule/SOP paths
-> apply those paths as an overlay to the user request
-> model answers or acts
```

Do not read large directories or full memory files during normal work.

## Routing Hit

When routing returns relevant paths:

1. Read only returned paths.
2. Treat their prompts, rules, SOPs, and preferences as extra instructions.
3. Combine them with the user's current request.
4. Execute normally.
5. Log what was useful when practical.

## Routing Miss

When routing returns no paths:

1. Do not stop the conversation.
2. Treat the request as new content.
3. Answer or act normally.
4. Log concise candidates only when they may help future tasks.

## Nightly Organization

Nightly maintenance runs outside normal conversation:

- groups repeated user preferences into rules,
- turns repeated workflows into SOPs,
- updates `workspace/memory/index.json`,
- moves stale entries from hot to warm or cold,
- keeps top-level indexes short,
- reports what changed to the user.

## User Value

Over time the model should:

- ask fewer repeated questions,
- follow the user's preferred style,
- remember stable local workflows,
- load less context,
- feel more personalized without reading full chat history.
