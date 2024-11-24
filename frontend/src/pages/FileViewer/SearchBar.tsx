import ClearIcon from "@mui/icons-material/Clear";
import SearchIcon from "@mui/icons-material/Search";
import { Box, Input, Paper, Popover, Typography } from "@mui/material";
import {
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import "../../index.css";
import { SelectedDirectoryContext } from "../../utils/directoryctx";
import { getSuggestions } from "./searchSuggestions";
type Props = {
  initialQuery: string;
  onSearch: (query: string) => void;
  onEmptyEnter?: () => void;
};

export const SearchBar = ({ initialQuery, onSearch, onEmptyEnter }: Props) => {
  const directory = useContext(SelectedDirectoryContext) ?? "";
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);
  const [suggestions, setSuggestions] = useState<
    { wholeWord: string; remainder: string }[]
  >([]);
  const [highlightedSuggestionIdx, setHighlightedSuggestionIdx] =
    useState<number>(0);
  const [showClear, setShowClear] = useState(initialQuery !== "");

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
    setAnchorEl(inputRef.current);
  };

  const handlePopoverClose = () => {
    setAnchorEl(null);
  };
  const [query, setQuery] = useState(initialQuery);
  const inputRef = useRef(null);

  useLayoutEffect(() => {
    if (inputRef.current) {
      (inputRef.current as any).focus();
    }
  }, []);

  useEffect(() => {
    setQuery(initialQuery);
  }, [directory, initialQuery]);

  const triggerSearch = () => {
    handlePopoverClose();
    if (query === "" && onEmptyEnter) {
      onEmptyEnter();
      setShowClear(false);
    } else {
      onSearch(query);
      if (query.trim() !== "") {
        setShowClear(true);
      }
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
        {showClear && (
          <Box
            onClick={() => {
              setQuery("");
              onEmptyEnter?.();
              setShowClear(false);
            }}
          >
            <ClearIcon
              className="searchIcon"
              sx={{
                ml: 1,
                mr: -0.5,
              }}
            />
          </Box>
        )}
        {showClear && (
          <div
            style={{
              width: "2px",
              height: "24px",
              background: "#ebebeb",
              opacity: "0.5",
              marginLeft: "12px",
            }}
          />
        )}
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
            660
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
