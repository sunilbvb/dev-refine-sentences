/**
 * Linguistic Readability Metrics Calculator
 * Implements Flesch Reading Ease & Flesch-Kincaid Grade Level.
 */

window.MetricsCalculator = {
  countSyllables: function(word) {
    word = word.toLowerCase().replace(/[^a-z]/g, '');
    if (!word) return 0;
    if (word.length <= 3) return 1;

    word = word.replace(/(?:[^laeiouy]|ed|es|e)$/, '');
    word = word.replace(/^y/, '');
    const matches = word.match(/[aeiouy]{1,2}/g);
    return matches ? matches.length : 1;
  },

  analyze: function(text) {
    if (!text || !text.trim()) {
      return { words: 0, sentences: 0, syllables: 0, readingEase: 100, gradeLevel: 0, readingTimeSec: 0 };
    }

    const sentences = text.split(/[.!?]+/).map(s => s.trim()).filter(Boolean);
    const numSentences = Math.max(sentences.length, 1);

    const words = text.trim().split(/\s+/).map(w => w.replace(/[^A-Za-z0-9]/g, '')).filter(Boolean);
    const numWords = Math.max(words.length, 1);

    let numSyllables = 0;
    for (const w of words) {
      numSyllables += this.countSyllables(w);
    }

    const asl = numWords / numSentences;
    const asw = numSyllables / numWords;

    let readingEase = 206.835 - (1.015 * asl) - (84.6 * asw);
    readingEase = Math.max(0, Math.min(100, Math.round(readingEase * 10) / 10));

    let gradeLevel = (0.39 * asl) + (11.8 * asw) - 15.59;
    gradeLevel = Math.max(0, Math.round(gradeLevel * 10) / 10);

    const readingTimeSec = Math.round((numWords / 200) * 60);

    return {
      words: numWords,
      sentences: numSentences,
      syllables: numSyllables,
      readingEase: readingEase,
      gradeLevel: gradeLevel,
      readingTimeSec: Math.max(1, readingTimeSec)
    };
  }
};
