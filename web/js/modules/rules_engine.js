/**
 * Client-Side Offline Rule-Based Refiner
 * Mirrors Python refiner/rules.py for instant local simulation without server.
 */

window.BrowserRefiner = {
  TYPOS: {
    "\\bi\\b": "I",
    "\\bdont\\b": "don't",
    "\\bcant\\b": "can't",
    "\\bwont\\b": "won't",
    "\\bdidnt\\b": "didn't",
    "\\bisnt\\b": "isn't",
    "\\bteh\\b": "the",
    "\\brecieve\\b": "receive",
    "\\bdefinately\\b": "definitely",
    "\\bthx\\b": "thanks",
    "\\bplz\\b": "please",
    "\\bpls\\b": "please",
    "\\basap\\b": "as soon as possible",
    "\\bbtw\\b": "by the way",
    "\\bfyi\\b": "for your information",
    "\\brn\\b": "right now",
    "\\btmrw\\b": "tomorrow",
    "\\bmsg\\b": "message",
    "\\bu\\b": "you",
    "\\br\\b": "are",
    "\\bur\\b": "your"
  },

  GRAMMAR: [
    { pattern: "\\bi\\s+is\\b", replacement: "I am", reason: "Subject-verb agreement: 'I' pairs with 'am'." },
    { pattern: "\\bhe\\s+are\\b", replacement: "he is", reason: "Subject-verb agreement: 'he' pairs with 'is'." },
    { pattern: "\\bthey\\s+is\\b", replacement: "they are", reason: "Subject-verb agreement: 'they' pairs with 'are'." },
    { pattern: "\\bhe\\s+go\\b", replacement: "he goes", reason: "Subject-verb agreement: third-person singular uses 'goes'." },
    { pattern: "\\bbuyed\\b", replacement: "bought", reason: "Irregular verb: 'buy' past tense is 'bought'." },
    { pattern: "\\bgoed\\b", replacement: "went", reason: "Irregular verb: 'go' past tense is 'went'." },
    { pattern: "\\bdo not hesitated\\b", replacement: "do not hesitate", reason: "Auxiliary verb 'do' requires base infinitive." },
    { pattern: "\\bwrote\\s+down\\b", replacement: "written down", reason: "Passive voice participle correction." }
  ],

  CONCISE: [
    { pattern: "\\bin\\s+order\\s+to\\b", replacement: "to", reason: "Conciseness: 'in order to' shortened to 'to'." },
    { pattern: "\\bbasically\\b", replacement: "", reason: "Conciseness: Removed filler word 'basically'." },
    { pattern: "\\bat\\s+the\\s+present\\s+time\\b", replacement: "now", reason: "Conciseness: 'at the present time' replaced with 'now'." },
    { pattern: "\\bdue\\s+to\\s+the\\s+fact\\s+that\\b", replacement: "because", reason: "Conciseness: Replaced wordy phrase with 'because'." }
  ],

  PROFESSIONAL: [
    { pattern: "\\bgonna\\b", replacement: "going to", reason: "Professionalism: Replaced informal contraction 'gonna'." },
    { pattern: "\\bwanna\\b", replacement: "want to", reason: "Professionalism: Replaced informal contraction 'wanna'." },
    { pattern: "\\bgive\\s+me\\s+a\\s+shout\\b", replacement: "contact me", reason: "Professionalism: Formalized contact request." },
    { pattern: "\\bhey\\b", replacement: "hello", reason: "Professionalism: Elevated greeting." }
  ],

  FRIENDLY: [
    { pattern: "\\bhello\\b", replacement: "hey there", reason: "Tone: Made greeting casual and warm." },
    { pattern: "\\bdo\\s+not\\s+hesitate\\b", replacement: "feel free", reason: "Tone: Made phrasing approachable." }
  ],

  refine: function(text, tone = "standard") {
    if (!text || !text.trim()) {
      return { refined: "", explanations: [] };
    }

    let result = text.trim();
    const explanations = [];

    // Step 1: Expand Dynamic Snippets
    const now = new Date();
    result = result.replace(/\{\{date\}\}/gi, () => {
      explanations.push("Snippet: Expanded {{date}}.");
      return now.toISOString().split('T')[0];
    });
    result = result.replace(/\{\{year\}\}/gi, () => {
      explanations.push("Snippet: Expanded {{year}}.");
      return now.getFullYear().toString();
    });

    // Step 2: Typos & Shorthands
    for (const [pat, rep] of Object.entries(this.TYPOS)) {
      const rx = new RegExp(pat, "gi");
      if (rx.test(result)) {
        result = result.replace(rx, rep);
        explanations.push(`Spelling: Expanded typo/shorthand '${pat.replace(/\\b/g, '')}' → '${rep}'.`);
      }
    }

    // Step 3: Grammar
    for (const g of this.GRAMMAR) {
      const rx = new RegExp(g.pattern, "gi");
      if (rx.test(result)) {
        result = result.replace(rx, g.replacement);
        explanations.push(`Grammar: ${g.reason}`);
      }
    }

    // Step 4: Tone transformations
    if (tone === "concise") {
      for (const c of this.CONCISE) {
        const rx = new RegExp(c.pattern, "gi");
        if (rx.test(result)) {
          result = result.replace(rx, c.replacement);
          explanations.push(c.reason);
        }
      }
    } else if (tone === "professional") {
      for (const p of this.PROFESSIONAL) {
        const rx = new RegExp(p.pattern, "gi");
        if (rx.test(result)) {
          result = result.replace(rx, p.replacement);
          explanations.push(p.reason);
        }
      }
    } else if (tone === "friendly") {
      for (const f of this.FRIENDLY) {
        const rx = new RegExp(f.pattern, "gi");
        if (rx.test(result)) {
          result = result.replace(rx, f.replacement);
          explanations.push(f.reason);
        }
      }
    }

    // Step 5: Duplicate words ("the the" -> "the")
    const dupRx = /\b(\w+)\s+\1\b/gi;
    if (dupRx.test(result)) {
      result = result.replace(dupRx, "$1");
      explanations.push("Redundancy: Removed repeated word.");
    }

    // Step 6: Punctuation cleanup
    result = result.replace(/\s+([,.:;?!])/g, "$1");
    result = result.replace(/([,.:;?!])([A-Za-z])/g, "$1 $2");
    result = result.replace(/([!?,]){2,}/g, "$1");
    result = result.replace(/[ \t]+/g, " ").trim();

    // Step 7: Capitalize first letter of sentences
    if (result) {
      result = result.charAt(0).toUpperCase() + result.slice(1);
      result = result.replace(/([.!?]\s+)([a-z])/g, (m, p1, p2) => p1 + p2.toUpperCase());
    }

    // Step 8: Ensure closing punctuation
    if (result && !/[.!?]$/.test(result)) {
      result += ".";
      explanations.push("Punctuation: Added closing punctuation mark ('.').");
    }

    // Tone specific formatting
    if (tone === "bullet_points") {
      const parts = result.split(/(?<=[.!?])\s+/).filter(Boolean);
      result = parts.map(s => `- ${s}`).join("\n");
      explanations.push("Formatting: Formatted as bulleted items.");
    } else if (tone === "email_formal") {
      result = `Hi team,\n\n${result}\n\nBest regards,`;
      explanations.push("Structure: Added professional email greeting and sign-off.");
    }

    return { refined: result, explanations: explanations };
  }
};
