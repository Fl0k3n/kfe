const FILE_TYPE_SUGGESTIONS = ["image", "video", "audio", "ss", "!ss"];

const SEARCH_METRIC_SUGGESTIONS = [
  "lex",
  "sem",
  "dlex",
  "olex",
  "tlex",
  "dsem",
  "osem",
  "tsem",
  "clip",
  "clipv",
];

const VALID_MERGES: { [key: string]: string[] } = {
  ...Object.fromEntries(
    SEARCH_METRIC_SUGGESTIONS.filter((x) => x !== "clip" && x !== "clipv").map(
      (x) => [x, FILE_TYPE_SUGGESTIONS]
    )
  ),
  clip: ["ss", "!ss"],
  clipv: [],
  ...Object.fromEntries(
    FILE_TYPE_SUGGESTIONS.filter(
      (x) => x !== "ss" && x !== "!ss" && x !== "image"
    ).map((x) => [x, SEARCH_METRIC_SUGGESTIONS.filter((v) => v !== "clip")])
  ),
  ss: SEARCH_METRIC_SUGGESTIONS,
  image: [...SEARCH_METRIC_SUGGESTIONS, "!ss"],
  "!ss": [...SEARCH_METRIC_SUGGESTIONS, "image"],
};

const ALL_SUGGESTIONS = [
  ...FILE_TYPE_SUGGESTIONS,
  ...SEARCH_METRIC_SUGGESTIONS,
];

export type Suggestion = {
  wholeWord: string;
  remainder: string;
};

export const getSuggestions = (
  fullQuery: string,
  prefix: string
): Suggestion[] => {
  const presentKeywords = fullQuery
    .split(" ")
    .filter((x) => x.startsWith("@"))
    .map((x) => x.substring(1, x.length))
    .filter((x) => ALL_SUGGESTIONS.includes(x));

  const possibleContinuations = ALL_SUGGESTIONS.filter((x) =>
    x.startsWith(prefix)
  )
    .filter((x) => !presentKeywords.includes(x))
    .filter((x) =>
      presentKeywords
        .map((presentKeyword) => VALID_MERGES[presentKeyword]?.includes(x))
        .every((passes) => passes)
    );

  const suggestions = possibleContinuations.map((x) => ({
    wholeWord: x,
    remainder: x.substring(prefix.length, x.length),
  }));
  suggestions.sort((a, b) => a.remainder.length - b.remainder.length);
  return suggestions.slice(0, 5);
};
