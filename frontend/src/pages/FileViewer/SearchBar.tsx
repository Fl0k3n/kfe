import SearchIcon from "@mui/icons-material/Search";
import { Box, Input, Paper, Popover, Typography } from "@mui/material";
import { useLayoutEffect, useRef, useState } from "react";
import "../../index.css";
import { getSuggestions } from "./SearchSuggestions";

type Props = {
  onSearch: (query: string) => void;
  onEmptyEnter?: () => void;
};

export const SearchBar = ({ onSearch, onEmptyEnter }: Props) => {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [suggestions, setSuggestions] = useState<
    { wholeWord: string; remainder: string }[]
  >([]);
  const [highlightedSuggestionIdx, setHighlightedSuggestionIdx] =
    useState<number>(0);

  const updateSuggestions = (text: string) => {
    const words = text.split(" ");
    if (words.length === 0) {
      handlePopoverClose();
      return;
    }
    const word = words[words.length - 1];
    if (!word.startsWith("@")) {
      handlePopoverClose();
      return;
    }
    setHighlightedSuggestionIdx(0);
    setSuggestions(getSuggestions(query, word.substring(1, word.length)));
    setAnchorEl(inputRef.current as any);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);

  useLayoutEffect(() => {
    if (inputRef.current) {
      (inputRef.current as any).focus();
    }
  }, []);

  const triggerSearch = () => {
    if (query === "" && onEmptyEnter) {
      onEmptyEnter();
    } else {
      onSearch(query);
    }
  };

  const suggestionsOpen = !!anchorEl && suggestions.length > 0;

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        flexDirection: "row",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Paper
        elevation={3}
        sx={{
          width: "100%",
          p: 1,
          px: 2,
          background: "rgba(41, 141, 255, 0.39)",
          display: "flex",
          flexDirection: "row",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Input
          inputRef={inputRef}
          fullWidth
          disableUnderline
          sx={{ borderRadius: "20px", color: "white" }}
          value={query}
          onChange={(e) => {
            updateSuggestions(e.target.value);
            setQuery(e.target.value);
          }}
          onKeyUp={(e) => {
            if (e.key === "Enter") {
              triggerSearch();
            }
          }}
          onKeyDown={(e) => {
            if (!suggestionsOpen) return;
            if (e.key === "Tab") {
              e.preventDefault();
              const newText =
                query + suggestions[highlightedSuggestionIdx].remainder + " ";
              setQuery(newText);
              handlePopoverClose();
            }
            if (e.key === "ArrowDown") {
              setHighlightedSuggestionIdx(
                (idx) => (idx + 1) % suggestions.length
              );
            }
            if (e.key === "ArrowUp") {
              setHighlightedSuggestionIdx(
                (idx) => (idx + suggestions.length - 1) % suggestions.length
              );
            }
          }}
        />
        <Box onClick={() => triggerSearch()}>
          <SearchIcon
            className="searchIcon"
            sx={{
              ml: 1,
              mr: -0.5,
            }}
          />
        </Box>
      </Paper>
      <Popover
        open={suggestionsOpen}
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
        transformOrigin={{
          vertical: "top",
          horizontal: "left",
        }}
        onClose={handlePopoverClose}
        disableAutoFocus
        sx={{
          ml: `${Math.min(
            query.length * 9 -
              query
                .split("")
                .filter((x) => ["i", "I", "l", "f", "j", "1"].includes(x))
                .length *
                7,
            700
          )}px`, // TODO more robust way to approximate cursor position
        }}
      >
        {suggestions.map((suggestion, i) => (
          <Typography
            sx={{ p: 0.5, textAlign: "left" }}
            key={suggestion.wholeWord}
            bgcolor={i === highlightedSuggestionIdx ? "#b6b6b6" : "white"}
          >
            {suggestion.wholeWord}
          </Typography>
        ))}
      </Popover>
    </Box>
  );
};
