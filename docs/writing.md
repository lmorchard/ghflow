# Writing rules

On 2026-09-30, Les requested a trial of ASD-STE100 for documents and specifications. ASD-STE100 is a standard for simplified technical English. The trial uses the strict mode of the simple-english skill.

On 2026-10-02, Les limited strict mode to documents, specifications, and issue text. Skills follow the plainer [Skill style](dev/skill-style.md). In skills, the strict rules repeated term definitions and split related conditions into separate sentences.

The skill does not contain the full official dictionary. No tool guarantees compliance. These documents apply the available guidance, but they do not claim full compliance.

## Sentence structure

Use commands for instructions. Put a condition before its instruction. Give one instruction in each sentence.

Use a maximum of 20 words in an instruction sentence. Use a maximum of 25 words in a description sentence. Keep each paragraph to one subject and a maximum of six sentences.

Use active voice and simple tenses. Name the person or tool that does the action. Do not use contractions, semicolons, or em dashes in prose.

## Words and technical terms

Use one word for one meaning. Use “make sure that” for a required state. Use “examine” when the reader must look for errors.

Define a necessary technical term at its first use in each document. Keep the definition short. Do not change command names, paths, API fields, product names, or quoted errors.

The official dictionary controls approved words, meanings, and grammar. The skill supplies only part of that guidance. If a word is uncertain, use a simpler word or record the need for a dictionary review.

## Setup documents

A setup document can describe mutable state, such as installed links, worktrees, identity readiness, tokens, ports, and local services.
Name the command that checks each mutable state and the expected result.
Do not assert the current state.

For example, check the OpenCode checkout with:

```sh
git -C ~/.agents/skills/ghflow worktree list
```

The expected result is one line for the checkout.

## Specifications

Keep proposals separate from requirements. Use “must” only for a requirement. To describe a proposal, start with “We propose” or identify the section as a proposal.

For each requirement, name the actor, condition, action, and expected result when these apply. State how a person can determine whether the result meets the requirement. If human judgment is necessary, say so.

Do not change scope, permission, or certainty to shorten a sentence. Do not replace an uncertain statement with a requirement. Keep the original fact when the source gives no cause or number.

## Review of the trial

Read the revised document for meaning before you examine its style. Make sure that decisions remain decisions and proposals remain proposals. Make sure that technical names and source links remain correct.

Record wording that becomes harder to read under the strict rules. Do not treat sentence length as proof of clarity. Use real documents and specifications to decide whether to keep strict mode or return to plain English.
