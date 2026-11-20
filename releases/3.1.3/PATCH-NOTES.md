# 3.1.3 Patch Release

- Upgrades the static expression linter to normalize punctuation before phrase matching.
- Adds explicit detection for ambiguous colloquial phrases such as “成片如牛来”, and flags cover/opening echo.
- This static check supplements, but does not replace, semantic review of the promise chain and natural spoken language.
- No change to the 3.0.0 spoken-batch contract or the 3.1.1 AI-video production schema.
