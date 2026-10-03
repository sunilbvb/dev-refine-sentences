/**
 * Word Diff Tokenizer & Renderer
 * Computes word-by-word differences between original and refined strings.
 */

window.DiffHighlighter = {
  computeWordDiff: function(original, refined) {
    if (!original && !refined) return "";
    if (!original) return `<span class="diff-add">${this.escape(refined)}</span>`;
    if (!refined) return `<span class="diff-del">${this.escape(original)}</span>`;
    if (original === refined) return `<span class="diff-clean">${this.escape(refined)}</span>`;

    const origWords = this.tokenize(original);
    const refWords = this.tokenize(refined);

    // Simple LCS-based diff for words
    const lcs = this.getLCS(origWords, refWords);
    let i = 0, j = 0;
    let html = [];

    for (let k = 0; k < lcs.length; k++) {
      const match = lcs[k];
      while (i < match.i) {
        html.push(`<span class="diff-del">${this.escape(origWords[i])}</span>`);
        i++;
      }
      while (j < match.j) {
        html.push(`<span class="diff-add">${this.escape(refWords[j])}</span>`);
        j++;
      }
      html.push(`<span class="diff-clean">${this.escape(origWords[i])}</span>`);
      i++;
      j++;
    }

    while (i < origWords.length) {
      html.push(`<span class="diff-del">${this.escape(origWords[i])}</span>`);
      i++;
    }
    while (j < refWords.length) {
      html.push(`<span class="diff-add">${this.escape(refWords[j])}</span>`);
      j++;
    }

    return html.join(" ");
  },

  tokenize: function(text) {
    return text.trim().split(/\s+/).filter(w => w.length > 0);
  },

  getLCS: function(a, b) {
    const m = a.length, n = b.length;
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));

    for (let i = 0; i < m; i++) {
      for (let j = 0; j < n; j++) {
        if (a[i].toLowerCase() === b[j].toLowerCase()) {
          dp[i + 1][j + 1] = dp[i][j] + 1;
        } else {
          dp[i + 1][j + 1] = Math.max(dp[i + 1][j], dp[i][j + 1]);
        }
      }
    }

    let i = m, j = n;
    const matches = [];
    while (i > 0 && j > 0) {
      if (a[i - 1].toLowerCase() === b[j - 1].toLowerCase()) {
        matches.push({ i: i - 1, j: j - 1 });
        i--;
        j--;
      } else if (dp[i - 1][j] >= dp[i][j - 1]) {
        i--;
      } else {
        j--;
      }
    }
    return matches.reverse();
  },

  escape: function(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
  }
};
