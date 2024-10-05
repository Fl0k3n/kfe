import { Box, TextField } from "@mui/material";
import { useState } from "react";

type Props = {
  onSearch: (query: string) => void;
  onEmptyEnter?: () => void;
};

export const SearchBar = ({ onSearch, onEmptyEnter }: Props) => {
  const [query, setQuery] = useState("");
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
      <Box sx={{ width: "100%", background: "#aaa" }}>
        <TextField
          fullWidth
          variant="outlined"
          sx={{ borderRadius: "20px" }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyUp={(e) => {
            if (e.key === "Enter") {
              if (query === "" && onEmptyEnter) {
                onEmptyEnter();
              } else {
                onSearch(query);
              }
            }
          }}
        />
      </Box>
    </Box>
  );
};
