---
name: research-summarizer
description: Research any topic by searching the web, or summarize a document the user uploads or pastes. Use when user says "research X", "summarize this", "tell me about X", "what is X", sends a file, or pastes text to summarize. Also activated when ai-tutor needs deeper background content.
allowed-tools: WebSearch, WebFetch, Read
---

Provide a structured, well-formatted summary for any topic or document.

## Input Types

### Text topic ("research X" / "tell me about X" / "what is X")
1. WebSearch for 3–5 high-quality sources on the topic
2. WebFetch the 2 most relevant results for deeper detail
3. Synthesize findings into the response format below

### Uploaded file (user sends a PDF, .txt, or document via Telegram)
- Telegram downloads files to `~/.claude/channels/telegram/inbox/`
- Read the most recently modified file in that directory
- Extract and summarize key points from its content

### Pasted text
- User pastes content directly in the chat
- Summarize it using the response format below

## Response Format

Use Telegram Markdown formatting (`*bold*` renders in Telegram):

```
*[Topic or Document Title]*

*Summary:* 2–3 sentence overview of the subject.

*Key Points:*
• Point 1
• Point 2
• Point 3
• Point 4 (if applicable)

*Key Terms:* Term1, Term2, Term3

*Sources:* (web research only)
• Source Name — URL
```

## Rules
- Keep total response under 1800 characters; if longer, split into *Part 1* and *Part 2*
- State your assumption if the topic is ambiguous, then proceed
- If no good web sources are found, share what you did find and note the limitation
- Bullet points with • (not dashes) for visual clarity in Telegram

## Skill Chaining — Research then Teach

If the user says "research X and teach me", "research X and make a lesson", or "learn about X":
1. Run the full research flow above to gather information
2. Reply with the summary
3. Then immediately continue: "Starting lesson on [topic]..."
4. Build a structured lesson from the research findings:
   - *What is it?* (1–2 sentences)
   - *Why it matters* (real-world relevance)
   - *Core concepts* (3–5 bullet points)
   - *Example* (concrete analogy or use case)
   - *Check your understanding:* (1 quiz question)
