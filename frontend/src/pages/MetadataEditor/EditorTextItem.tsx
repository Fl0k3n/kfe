import { Box, Button, TextField, Typography } from "@mui/material";
import { useLayoutEffect, useState } from "react";

type Props = {
  name: string;
  value?: string;
  onValueChange: (newValue: string) => void;
  onUpdate: () => void;
};

export const EditorTextItem = ({
  name,
  value,
  onValueChange,
  onUpdate,
}: Props) => {
  const [multiline, setMultiline] = useState(false);
  useLayoutEffect(() => {
    setMultiline(true);
  }, []);
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "row",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <Typography variant="body1" sx={{ mr: 1, width: "130px" }}>
        {name}
      </Typography>
      <Box
        sx={{
          width: "90%",
          color: "white",
        }}
      >
        <TextField
          multiline={multiline}
          fullWidth
          rows={5}
          color="primary"
          inputProps={{
            style: { color: "#eee" },
          }}
          value={value}
          onChange={(e) => {
            onValueChange(e.target.value);
          }}
        />
      </Box>

      <Button
        sx={{ ml: 5, width: "120px", p: 1 }}
        variant="contained"
        onClick={() => {
          onUpdate();
        }}
      >
        Update
      </Button>
    </Box>
  );
};
