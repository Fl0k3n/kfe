import { Box, TextField } from "@mui/material";
import { useState } from "react";

type Props = {
  onSearch: (query: string) => void;
};

const ENTER_KEY_CODE = 13;

export const SearchBar = ({ onSearch }: Props) => {
  const [query, setQuery] = useState("");
  return (
    <Box sx={{ width: "100%", background: "#aaa" }}>
      <TextField
        fullWidth
        variant="outlined"
        sx={{ borderRadius: "20px" }}
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyUp={(e) => {
          if (e.key === "Enter") {
            onSearch(query);
          }
        }}
      />
    </Box>
  );
};
