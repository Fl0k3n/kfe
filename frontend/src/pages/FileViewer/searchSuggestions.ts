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
  "llm",
];

const VALID_MERGES: { [key: string]: string[] } = {
  ...Object.fromEntries(
    ["lex", "sem", "dlex", "dsem"].map((x) => [x, FILE_TYPE_SUGGESTIONS])
  ),
  ...Object.fromEntries(["olex", "osem"].map((x) => [x, []])),
  ...Object.fromEntries(["tlex", "tsem"].map((x) => [x, ["video", "audio"]])),
  clip: ["ss", "!ss", "image", "video"],
  llm: ["ss", "!ss", "image", "video"],
  image: [
    ...SEARCH_METRIC_SUGGESTIONS.filter((x) => x !== "tlex" && x !== "tsem"),
    "!ss",
  ],
  video: SEARCH_METRIC_SUGGESTIONS.filter((x) => x !== "olex" && x !== "osem"),
  audio: SEARCH_METRIC_SUGGESTIONS.filter(
    (x) => x !== "clip" && x !== "olex" && x !== "osem" && x !== "llm"
  ),
  ss: SEARCH_METRIC_SUGGESTIONS.filter((x) => x !== "tsem" && x !== "tlex"),
  "!ss": [...SEARCH_METRIC_SUGGESTIONS, "image"],
};

const TOP_SUGGESTIONS = ["clip", "lex", "sem", "image", "video"];

const ALL_SUGGESTIONS = [
  ...TOP_SUGGESTIONS,
  ...FILE_TYPE_SUGGESTIONS.filter(
    (x) => TOP_SUGGESTIONS.find((y) => y === x) == null
  ),
  ...SEARCH_METRIC_SUGGESTIONS.filter(
    (x) => TOP_SUGGESTIONS.find((y) => y === x) == null
  ),
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
  if (
    presentKeywords.length > 1 ||
    (presentKeywords.length === 1 && presentKeywords[0].length > 0)
  ) {
    suggestions.sort((a, b) => a.remainder.length - b.remainder.length);
  }
  return suggestions.slice(0, 5);
};
